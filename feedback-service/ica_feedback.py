"""
ica_feedback.py  --  Improving Cybersecurity Awareness (ICA)

Email analysis + feedback engine for the AI phishing simulator.

What it does
------------
1. analyse_email(raw_text)  -> finds red flags INSIDE the email itself
   (urgency / threats / requests for sensitive info / suspicious links /
   brand impersonation / generic greeting ...), keeping the exact wording
   found so feedback can quote the email back to the user.
2. extract_features(raw_text) -> numeric features for the ML model.
3. FeedbackEngine.analyse(raw_text) -> ML verdict + detailed, email-specific
   feedback (a JSON-friendly dict) that a website can display.
4. render_markdown(result) -> the same feedback as readable Markdown.

No external APIs are used - everything is rule-based analysis on top of the
trained scikit-learn model.
"""
import html
import re
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack

MAX_CHARS = 30000  # analysis cap per email, keeps very long emails fast


# --------------------------------------------------------------------------
# 1. Text preparation
# --------------------------------------------------------------------------
def clean_text(text):
    """Cleaned text used as input for the TF-IDF vectoriser."""
    text = html.unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"http\S+|www\.\S+", " URL ", text)
    text = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", " ", text)   # drop addresses (dataset artefact: recipient jose@monkey.org)
    text = re.sub(r"(?i)\bmonkey(?:\.org)?\b|\bjose\b", " ", text)    # recipient artefact in the human phishing emails
    return re.sub(r"\s+", " ", text).strip()


def prepare_text(raw):
    """Return (plain_text, anchors). Anchors are (href, shown_text) pairs from any HTML."""
    raw = str(raw)[:MAX_CHARS]
    anchors = []
    for m in re.finditer(r"<a\s[^>]*?href=[\"']?([^\"'\s>]+)[\"']?[^>]*>(.*?)</a>", raw, re.I | re.S):
        shown = re.sub(r"<[^>]+>", " ", m.group(2))
        anchors.append((html.unescape(m.group(1)), re.sub(r"\s+", " ", html.unescape(shown)).strip()))
    plain = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = html.unescape(plain)
    plain = re.sub(r"[ \t\r\f\v]+", " ", plain)
    plain = re.sub(r"\n\s*\n+", "\n\n", plain).strip()
    return plain, anchors


# --------------------------------------------------------------------------
# 2. Brands, domains and links
# --------------------------------------------------------------------------
BRANDS = {
    "paypal": ["paypal.com"],
    "chase": ["chase.com", "jpmorgan.com", "jpmorganchase.com"],
    "bank of america": ["bankofamerica.com"],
    "wells fargo": ["wellsfargo.com"],
    "citibank": ["citi.com", "citibank.com"],
    "amazon": ["amazon.com", "amazon.co.uk", "amazon.com.au", "amazon.ca", "amazon.de", "amazonaws.com"],
    "apple": ["apple.com", "icloud.com"],
    "microsoft": ["microsoft.com", "office.com", "office365.com", "live.com", "outlook.com",
                  "microsoftonline.com", "sharepoint.com"],
    "google": ["google.com", "gmail.com", "youtube.com"],
    "netflix": ["netflix.com"],
    "facebook": ["facebook.com", "fb.com", "facebookmail.com", "meta.com"],
    "instagram": ["instagram.com"],
    "linkedin": ["linkedin.com"],
    "dropbox": ["dropbox.com"],
    "docusign": ["docusign.com", "docusign.net"],
    "dhl": ["dhl.com"],
    "fedex": ["fedex.com"],
    "ebay": ["ebay.com"],
    "coinbase": ["coinbase.com"],
    "binance": ["binance.com"],
    "metamask": ["metamask.io"],
    "commonwealth bank": ["commbank.com.au"],
    "westpac": ["westpac.com.au"],
    "anz": ["anz.com", "anz.com.au"],
    "mygov": ["my.gov.au"],
    "australia post": ["auspost.com.au"],
    "ato": ["ato.gov.au"],
}
EXTRA_DOMAIN_TOKENS = {"commonwealth bank": ["commbank"], "australia post": ["auspost"]}
OFFICIAL_DOMAINS = {d for ds in BRANDS.values() for d in ds}

# brand name -> tokens to look for inside a link's host name (3-letter names are too ambiguous)
BRAND_TOKENS = {}
for _name in BRANDS:
    _tokens = [_name.replace(" ", "")] + EXTRA_DOMAIN_TOKENS.get(_name, [])
    _tokens = [t for t in _tokens if len(t) >= 4]
    if _tokens:
        BRAND_TOKENS[_name] = _tokens

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "rebrand.ly",
              "cutt.ly", "shorturl.at", "tiny.cc", "rb.gy", "t.ly"}
SUSPICIOUS_TLDS = {"xyz", "top", "tk", "ml", "ga", "cf", "gq", "icu", "click", "link", "work", "live",
                   "online", "site", "club", "vip", "shop", "support", "zip", "mov", "cam", "rest",
                   "buzz", "monster", "cyou", "sbs"}
DOMAIN_KEYWORDS = ["login", "signin", "secure", "verify", "verification", "account", "update", "auth",
                   "billing", "wallet", "support", "alert", "confirm", "recover", "unlock", "helpdesk"]
SECOND_LEVELS = {"co", "com", "org", "net", "gov", "edu", "ac"}

TLD_PATTERN = ("com|net|org|info|biz|xyz|top|club|online|site|co|io|ru|cn|tk|ml|ga|cf|gq|support|live|app|"
               "link|click|work|icu|vip|shop|store|us|uk|au|ca|de|fr|nl|gov|edu")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"'\)\]]+", re.I)
BARE_RE = re.compile(rf"\b(?:[a-z0-9][a-z0-9-]*\.)+(?:{TLD_PATTERN})\b(?:/[^\s<>\"'\)\]]*)?", re.I)
IP_RE = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")


def registered_domain(host):
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    if len(parts[-1]) == 2 and parts[-2] in SECOND_LEVELS:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def analyse_link(raw):
    """Inspect a single link/domain and describe anything suspicious about it."""
    link = raw.strip().rstrip(".,;:!?)>]}'\"")
    has_scheme = bool(re.match(r"https?://", link, re.I))
    try:
        parsed = urlparse(link if has_scheme else "http://" + link)
        host = (parsed.hostname or "").lower().strip(".")
        netloc = parsed.netloc
    except ValueError:
        return None
    if not host or "." not in host:
        return None

    domain = registered_domain(host)
    info = {"url": link, "host": host, "domain": domain, "issues": [], "brand": None,
            "official": domain in OFFICIAL_DOMAINS}
    issues = info["issues"]

    if has_scheme and link.lower().startswith("http://"):
        issues.append(("insecure", "uses unencrypted http:// instead of https://"))
    if "@" in netloc:
        issues.append(("userinfo", "contains an '@' before the real address, a trick used to disguise the true destination"))
    if info["official"]:
        return info

    if IP_RE.fullmatch(host):
        issues.append(("ip", "uses a raw IP address instead of a normal website name"))
    if domain in SHORTENERS:
        issues.append(("shortener", "is a link-shortening service, which hides the real destination"))
    if "xn--" in host:
        issues.append(("punycode", "uses encoded international characters that can imitate a real brand"))

    for brand, tokens in BRAND_TOKENS.items():
        if any(t in host for t in tokens):
            official = BRANDS[brand]
            if any(d in host for d in official):
                issues.append(("subdomain_trick",
                               f"puts '{official[0]}' inside the address, but the real domain is {domain}"))
            else:
                issues.append(("lookalike",
                               f"imitates {brand.title()} but is not an official {brand.title()} domain ({official[0]})"))
            info["brand"] = brand
            break

    label = domain.split(".")[0]
    if label.count("-") >= 2:
        issues.append(("hyphens", "uses several hyphens, which is common in made-up lookalike domains"))
    kws = [k for k in DOMAIN_KEYWORDS if k in label]
    if kws:
        issues.append(("keywords", f"includes words like '{kws[0]}' that are often used to look official"))
    tld = domain.split(".")[-1]
    if tld in SUSPICIOUS_TLDS:
        issues.append(("tld", f"ends in .{tld}, a domain type frequently abused in scams"))
    if len(host.split(".")) - len(domain.split(".")) >= 3:
        issues.append(("subdomains", "has an unusually long chain of subdomains"))
    return info


def extract_links(plain, anchors):
    """All links/domains in the email, each with its own list of issues."""
    found = {}
    no_emails = EMAIL_RE.sub(" ", plain)
    candidates = URL_RE.findall(no_emails)
    remainder = URL_RE.sub(" ", no_emails)
    candidates += [m.group(0) for m in BARE_RE.finditer(remainder)]
    candidates += [h for h, _ in anchors if re.match(r"(?:https?://|www\.)", h, re.I)]
    for cand in candidates:
        info = analyse_link(cand)
        if info and info["url"].lower() not in found:
            found[info["url"].lower()] = info

    # HTML links whose visible text shows one address but whose href goes elsewhere
    for href, shown in anchors:
        if not re.match(r"(?:https?://|www\.)", href, re.I):
            continue
        if not (URL_RE.search(shown) or BARE_RE.search(shown)):
            continue
        real = analyse_link(href)
        shown_link = analyse_link((URL_RE.search(shown) or BARE_RE.search(shown)).group(0))
        if real and shown_link and real["domain"] != shown_link["domain"]:
            entry = found.setdefault(real["url"].lower(), real)
            entry["issues"].append(("display_mismatch",
                                    f"is displayed as '{shown_link['domain']}' but actually leads to {real['domain']}"))
    return list(found.values())


# --------------------------------------------------------------------------
# 3. Phrase categories (social-engineering cues)
# --------------------------------------------------------------------------
def _compile(patterns):
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.I)


CATEGORIES = {
    "sensitive": {
        "title": "Asks for sensitive information", "severity": 3,
        "headline": "a request for sensitive details", "principle": "Information harvesting",
        "regex": _compile([
            r"\bpass(?:word|code)s?\b", r"(?-i:\bPIN\b)", r"\bsocial security\b", r"(?-i:\bSSN\b)",
            r"\btax file number\b", r"\bcredit card\b", r"\bdebit card\b", r"\bcard (?:number|details)\b",
            r"\bcvv\b", r"\b(?:bank )?account (?:number|details|information)\b", r"\brouting number\b",
            r"\blog-?in (?:details|credentials|information)\b", r"\bcredentials\b",
            r"\bverify your (?:identity|account|details|information|email|payment)\b",
            r"\bconfirm your (?:identity|account|details|information|email|password|payment)\b",
            r"\bupdate your (?:billing|payment|account|information|details|password|security)\b",
            r"\bpersonal (?:information|details|data)\b",
            r"\b(?:one[- ]time|verification|security|authentication) (?:code|password)\b",
            r"\botp\b", r"\bseed phrase\b", r"\brecovery phrase\b", r"\bprivate key\b",
            r"\bdate of birth\b", r"\bmother'?s maiden name\b"]),
        "why": ("Legitimate organisations almost never ask you to hand over passwords, card details or identity "
                "information by email. Attackers collect these details to take over accounts or commit fraud."),
        "action": ("Never send passwords, PINs or card details by email. If you are unsure, sign in by typing the "
                   "organisation's real address into your browser (or using its official app) and check for "
                   "alerts there."),
    },
    "urgency": {
        "title": "Creates time pressure", "severity": 2,
        "headline": "pressure to act quickly", "principle": "Urgency / scarcity",
        "regex": _compile([
            r"\burgent(?:ly)?\b", r"\bimmediately\b", r"\bimmediate (?:action|attention|response|payment)\b", r"\bright away\b", r"\bas soon as possible\b",
            r"\basap\b", r"\bwithin (?:the next )?\d+\s*(?:hours?|hrs?|days?|minutes?|mins?)\b",
            r"\bact (?:now|fast|quickly|immediately)\b", r"\bexpir(?:e|es|ed|ing|ation)\b",
            r"\blimited[- ]time\b", r"\blast chance\b", r"\bfinal (?:notice|warning|reminder)\b",
            r"\btime[- ]sensitive\b", r"\bwithout delay\b",
            r"\bfailure to (?:comply|respond|verify|act|update)\b", r"\bdeadline\b",
            r"\bbefore it(?:'s| is) too late\b", r"\bpromptly\b"]),
        "why": ("Rushing you is a classic social-engineering tactic. When you feel you must act straight away, you "
                "are less likely to stop and check whether the message is genuine."),
        "action": ("Pause before acting. Real organisations give reasonable time and rarely threaten consequences "
                   "within hours. Contact them using a phone number or website you already trust, not the details "
                   "in the email."),
    },
    "threat": {
        "title": "Threatens a negative consequence", "severity": 2,
        "headline": "threats about your account", "principle": "Fear",
        "regex": _compile([
            r"\bsuspend(?:ed)?\b", r"\bsuspension\b", r"\blocked\b", r"\bdeactivat(?:ed|ion)\b",
            r"\bterminat(?:ed|ion)\b", r"\bpermanently (?:closed|deleted|disabled)\b",
            r"\bclosed permanently\b", r"\bblocked\b", r"\brestricted\b", r"\bfrozen\b",
            r"\bunusual (?:activity|sign[- ]?in|login)\b", r"\bsuspicious (?:activity|sign[- ]?in|login)\b",
            r"\bunauthori[sz]ed\b", r"\bsecurity (?:alert|breach|incident|threat)\b", r"\bcompromised\b",
            r"\blegal action\b", r"\bpenalt(?:y|ies)\b", r"\bwill be (?:deleted|cancell?ed|removed)\b",
            r"\blose access\b", r"\bdata breach\b", r"\bfraudulent\b"]),
        "why": ("Fear is a powerful motivator. Warnings about suspended accounts, unusual activity or penalties are "
                "designed to make you react emotionally instead of logically."),
        "action": ("Do not click through to 'fix' the problem. Log in to the service directly (not via the email) "
                   "and check whether there is really an alert on your account."),
    },
    "money": {
        "title": "Involves payments or money transfers", "severity": 2,
        "headline": "a payment or money request", "principle": "Financial pressure",
        "regex": _compile([
            r"\bgift cards?\b", r"\bwire transfer\b", r"\bbitcoin\b", r"\bcrypto(?:currency)?\b",
            r"\bwestern union\b", r"\bpayment (?:is )?(?:overdue|due|failed|declined)\b",
            r"\boutstanding (?:balance|invoice|payment)\b", r"\bpay (?:now|immediately|the (?:fee|invoice))\b",
            r"\binvoice\b", r"\brefund\b", r"\btransfer (?:the )?funds?\b", r"\bprocessing fee\b"]),
        "why": ("Requests involving invoices, refunds, gift cards, crypto or wire transfers are common in fraud "
                "because payments are hard to reverse."),
        "action": ("Verify any payment request through a separate channel (for example, call the person or company "
                   "on a number you already know) before sending money or changing bank details."),
    },
    "lure": {
        "title": "Offers a reward or prize", "severity": 2,
        "headline": "an offer of a reward", "principle": "Greed / curiosity",
        "regex": _compile([
            r"\bcongratulations\b", r"\byou(?:'ve| have)? (?:been selected|won)\b", r"\bwinner\b", r"\bprize\b",
            r"\blottery\b", r"\bclaim your\b", r"\bexclusive (?:offer|deal|opportunity)\b",
            r"\binheritance\b", r"\bfree (?:gift|trial|money|iphone)\b", r"\bbonus\b",
            r"\bwork from home\b", r"\bearn \$?\d+", r"\bunclaimed\b"]),
        "why": ("Prizes, bonuses and 'exclusive' offers play on greed and curiosity. An unexpected reward you never "
                "applied for is a strong warning sign."),
        "action": "If you did not enter a competition or apply for the offer, treat it as suspicious and ignore it.",
    },
    "pretext": {
        "title": "Uses a familiar everyday pretext", "severity": 2,
        "headline": "a familiar pretext (shared document, delivery, voicemail...)", "principle": "Curiosity / familiarity",
        "regex": _compile([
            r"\b(?:has|have) been shared with you\b", r"\bshared (?:a|the) (?:document|file|folder)\b",
            r"\bview (?:the |shared )?(?:document|file|message|invoice)\b", r"\b(?:new|missed) voice ?(?:mail|message)\b",
            r"\bpackage (?:could not|couldn'?t|cannot) be delivered\b", r"\bdelivery (?:failed|attempt|notification)\b",
            r"\btracking number\b", r"\bscanned document\b", r"\be-?fax\b",
            r"\byou have (?:a |an )?(?:new |pending )?(?:message|document|fax|voicemail)\b",
            r"\bauto-?generated (?:email|message|notification)\b", r"\bdo not reply to this (?:email|message)\b"]),
        "why": ("Attackers disguise themselves as everyday notifications (a shared file, a voicemail, a parcel) "
                "because you are used to clicking these without thinking."),
        "action": ("If you were not expecting a file, voicemail or delivery, do not open it. Check directly in the "
                   "real service (for example your own OneDrive or the courier's app) instead of using the email."),
    },
    "action": {
        "title": "Pushes you to click, download or reply", "severity": 1,
        "headline": "instructions to click, download or reply", "principle": "Call to action",
        "regex": _compile([
            r"\bclick (?:here|the link|on the link|the button|below|on)\b", r"\bfollow (?:the|this) link\b",
            r"\b(?:log|sign)[- ]?in\b", r"\bdownload\b", r"\b(?:open|see|view|check) (?:the )?attach(?:ed|ment)\b",
            r"\breply (?:with|to this email)\b", r"\bcall (?:us|this number|our)\b",
            r"\bscan (?:the|this) qr\b", r"\bby clicking\b",
            r"\bvisit (?:the|our|this) (?:link|website|site|page)\b", r"\benable (?:macros|content)\b"]),
        "why": ("Phishing emails need you to do something (click, open a file, log in or reply) because that is "
                "where the attack actually happens."),
        "action": ("Do not click links or open attachments you were not expecting. Hover over a link to preview "
                   "where it really goes before deciding."),
    },
    "authority": {
        "title": "Leans on an official-sounding sender", "severity": 1,
        "headline": "an official-sounding sender", "principle": "Authority",
        "regex": _compile([
            r"\bsecurity team\b", r"\bsupport team\b", r"(?-i:\bIT\b) (?:department|team|support|helpdesk|help desk|administrator)",
            r"\bhelp ?desk\b", r"\badministrator\b", r"\bcompliance\b", r"\bfraud (?:department|team|prevention)\b",
            r"\bcustomer (?:service|support|care)\b", r"\baccount (?:security|services|team|department)\b",
            r"\bhuman resources\b", r"(?-i:\bHR\b)", r"\bchief executive\b", r"(?-i:\b(?:CEO|CFO)\b)",
            r"\bmanaging director\b", r"\bhead of [a-z]+(?: [a-z]+)?", r"\blegal department\b",
            r"\bofficial notice\b"]),
        "why": ("Attackers pose as security teams, IT, banks or senior staff because people are conditioned to "
                "comply with authority."),
        "action": ("Check who is really contacting you. Look at the sender's actual address and confirm unusual "
                   "requests with the person or department through a separate channel."),
    },
    "secrecy": {
        "title": "Asks for secrecy or confidentiality", "severity": 1,
        "headline": "a request for secrecy", "principle": "Isolation",
        "regex": _compile([
            r"\bconfidential\b", r"\bdo not (?:share|disclose|tell|forward)\b",
            r"\bkeep (?:this|it) (?:private|secret|between us|confidential)\b", r"\bdon'?t tell\b"]),
        "why": "Asking you to keep a request confidential isolates you from colleagues who might spot the scam.",
        "action": ("Be wary of requests that discourage you from checking with others. Talk to a colleague or your "
                   "IT/security team."),
    },
}

GENERIC_NAMES = (r"(?:valued\s+)?(?:customer|user|client|member|account\s+holder|account\s+owner|sir|madam|"
                 r"sir/madam|sir\s+or\s+madam|friend|employee|beneficiary|winner|applicant|subscriber|"
                 r"email\s+user|webmail\s+user|cardholder|colleague)s?")
GENERIC_GREETING_RE = re.compile(rf"\b(?:dear|hello|hi|greetings|attention)[\s,:]+{GENERIC_NAMES}\b", re.I)
PERSONAL_GREETING_RE = re.compile(r"\b(?:Dear|Hi|Hello|Hey)\s+((?:(?:Mr|Mrs|Ms|Miss|Dr|Prof)\.?\s+)?[A-Z][a-z]{2,15})\b")
NOT_NAMES = {"Customer", "User", "Client", "Member", "Sir", "Madam", "Valued", "Friend", "Employee", "All",
             "Everyone", "Team", "There", "Colleague", "Account", "Applicant", "Winner", "Beneficiary"}
SIGNOFF_RE = re.compile(
    r"(?:Sincerely|Regards|Best regards|Kind regards|Warm regards|Thank you|Thanks|Yours faithfully|"
    r"Yours sincerely|Respectfully|Best)[,\s]+(?:The\s+)?(?:[A-Z][\w&.'-]*\s+){0,4}"
    r"(?:Team|Department|Support|Services|Service|Security|Administration|Admin|Desk|Center|Centre|Division)\b")


def _hits(plain, regex):
    return [(m.group(0), m.start(), m.end()) for m in regex.finditer(plain)]


def analyse_email(raw_text):
    """Find every red flag in the email, keeping positions so we can quote the email back."""
    plain, anchors = prepare_text(raw_text)
    hits = {key: _hits(plain, spec["regex"]) for key, spec in CATEGORIES.items()}
    links = extract_links(plain, anchors)

    head = plain[:400]
    generic = GENERIC_GREETING_RE.search(head)
    personal = None
    if not generic:
        for m in PERSONAL_GREETING_RE.finditer(head):
            if m.group(1) not in NOT_NAMES:
                personal = m
                break
    signoff = SIGNOFF_RE.search(plain[-300:])

    # emails that open by naming a brand but link somewhere that brand does not own
    brand_issues = []
    covered = {l["brand"] for l in links if l["brand"]}
    head_l = plain[:500].lower()
    foreign = [l["domain"] for l in links if not l["official"]]
    for name, domains in BRANDS.items():
        if len(name) < 4 or name in covered:
            continue
        if re.search(rf"\b{re.escape(name)}\b", head_l) and foreign and not any(l["domain"] in domains for l in links):
            brand_issues.append({"brand": name, "official": domains[0], "domains": foreign[:3]})

    letters = [c for c in plain if c.isalpha()]
    upper_ratio = (sum(c.isupper() for c in letters) / len(letters)) if letters else 0.0
    return {
        "plain": plain, "hits": hits, "links": links,
        "generic_greeting": generic, "personal_greeting": personal, "signoff": signoff,
        "brand_issues": brand_issues, "exclamations": plain.count("!"), "upper_ratio": upper_ratio,
    }


# --------------------------------------------------------------------------
# 4. Numeric features for the ML model
# --------------------------------------------------------------------------
FEATURE_COLS = [
    "num_links", "num_suspicious_links", "sensitive_hits", "urgency_hits", "threat_hits", "money_hits",
    "lure_hits", "pretext_hits", "action_hits", "authority_hits", "secrecy_hits", "generic_greeting", "personal_greeting",
    "impersonal_signoff", "brand_mismatch", "exclamation_count", "uppercase_ratio", "log_length",
]


def features_from_analysis(a):
    suspicious = [l for l in a["links"] if any(code != "insecure" for code, _ in l["issues"])]
    return {
        "num_links": len(a["links"]),
        "num_suspicious_links": len(suspicious),
        "sensitive_hits": len(a["hits"]["sensitive"]),
        "urgency_hits": len(a["hits"]["urgency"]),
        "threat_hits": len(a["hits"]["threat"]),
        "money_hits": len(a["hits"]["money"]),
        "lure_hits": len(a["hits"]["lure"]),
        "pretext_hits": len(a["hits"]["pretext"]),
        "action_hits": len(a["hits"]["action"]),
        "authority_hits": len(a["hits"]["authority"]),
        "secrecy_hits": len(a["hits"]["secrecy"]),
        "generic_greeting": int(a["generic_greeting"] is not None),
        "personal_greeting": int(a["personal_greeting"] is not None),
        "impersonal_signoff": int(a["signoff"] is not None),
        "brand_mismatch": int(bool(a["brand_issues"]) or any(l["brand"] for l in a["links"])),
        "exclamation_count": a["exclamations"],
        "uppercase_ratio": a["upper_ratio"],
        "log_length": float(np.log1p(len(a["plain"]))),
    }


def extract_features(raw_text):
    return features_from_analysis(analyse_email(raw_text))


def featurise(texts):
    """DataFrame of model features for a pandas Series of raw email texts."""
    return pd.DataFrame([extract_features(t) for t in texts], index=texts.index)


# --------------------------------------------------------------------------
# 5. Feedback writing
# --------------------------------------------------------------------------
def _snippet(plain, start, end, radius=75):
    a, b = max(0, start - radius), min(len(plain), end + radius)
    s = re.sub(r"\s+", " ", plain[a:b].replace("\n", " ")).strip()
    if a > 0 and " " in s:
        s = s.split(" ", 1)[1]
    if b < len(plain) and " " in s:
        s = s.rsplit(" ", 1)[0]
    return ("..." if a > 0 else "") + s + ("..." if b < len(plain) else "")


def _evidence(plain, hits, limit=3):
    seen, out = set(), []
    for phrase, start, end in hits:
        key = phrase.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"phrase": phrase, "context": _snippet(plain, start, end)})
        if len(out) >= limit:
            break
    return out


def _join(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _quoted(items):
    return _join([f"\u201c{i}\u201d" for i in items])


TERM_DISPLAY = {"url": "[a link]"}


def _strength(value, top):
    ratio = abs(value) / top if top else 0
    return "strong" if ratio > 0.66 else "moderate" if ratio > 0.33 else "slight"


def build_flags(a):
    """Turn raw analysis into a list of detailed, email-specific red flags (most serious first)."""
    plain, flags = a["plain"], []

    # --- links ---
    bad_links = [l for l in a["links"] if any(code != "insecure" for code, _ in l["issues"])]
    insecure_only = [l for l in a["links"] if l["issues"] and l not in bad_links]
    if bad_links:
        strong_codes = {"ip", "userinfo", "lookalike", "subdomain_trick", "display_mismatch", "shortener", "punycode"}
        strong = any(code in strong_codes for l in bad_links for code, _ in l["issues"]) or \
            any(len(l["issues"]) >= 2 for l in bad_links)
        domains = list(dict.fromkeys(l["domain"] for l in bad_links))[:3]
        flags.append({
            "key": "links", "title": "Suspicious link" + ("s" if len(bad_links) > 1 else ""),
            "severity": 4 if strong else 2,
            "headline": f"a suspicious link ({_join(domains)})",
            "finding": (f"The email contains {len(a['links'])} link(s)/web address(es), and {len(bad_links)} of them "
                        f"{'looks' if len(bad_links) == 1 else 'look'} suspicious. The real destination of a link "
                        f"matters more than the words around it."),
            "evidence": [f"{l['url']}  --  this address " + "; it ".join(msg for _, msg in l["issues"][:3])
                         for l in bad_links[:3]],
            "why": ("Phishing links are built to look like a trusted site while sending you to a page controlled by "
                    "the attacker, where anything you type is stolen."),
            "action": ("Do not click it. Go to the organisation's website by typing its address yourself, or use its "
                       "official app. On a computer you can hover over a link to preview its destination."),
        })
    if insecure_only:
        flags.append({
            "key": "insecure", "title": "Unencrypted link" + ("s" if len(insecure_only) > 1 else ""), "severity": 1,
            "headline": "an unencrypted (http://) link",
            "finding": (f"{len(insecure_only)} link(s) use plain http:// instead of https://, so the connection is "
                        "not encrypted."),
            "evidence": [l["url"] for l in insecure_only[:3]],
            "why": ("Reputable organisations almost always use https://. An http:// link is not proof of a scam "
                    "(older sites still use it), but it is a reason to be careful with anything you type there."),
            "action": "Check the address carefully and never enter passwords or payment details on an http:// page.",
        })

    # --- brand impersonation without a matching link ---
    for issue in a["brand_issues"][:2]:
        flags.append({
            "key": "brand", "title": f"Mentions {issue['brand'].title()} but links elsewhere", "severity": 3,
            "headline": f"a link that doesn't belong to {issue['brand'].title()}",
            "finding": (f"The email opens by referring to {issue['brand'].title()}, yet its link(s) point to "
                        f"{_join(issue['domains'])} rather than {issue['official']}."),
            "evidence": [], "why": ("Attackers borrow a well-known name to earn your trust, then send you to a "
                                    "look-alike page."),
            "action": f"Check {issue['brand'].title()}'s own website or app directly instead of using this email's link.",
        })

    # --- phrase categories ---
    for key, spec in CATEGORIES.items():
        hits = a["hits"][key]
        if not hits:
            continue
        ev = _evidence(plain, hits)
        phrases = [e["phrase"].lower() for e in ev]
        flags.append({
            "key": key, "title": spec["title"], "severity": spec["severity"], "headline": spec["headline"],
            "principle": spec["principle"],
            "finding": f"The email uses wording such as {_quoted(phrases)}.",
            "evidence": [e["context"] for e in ev], "why": spec["why"], "action": spec["action"],
        })

    # --- greeting / sign-off ---
    if a["generic_greeting"]:
        g = a["generic_greeting"].group(0).strip(" ,:")
        flags.append({
            "key": "greeting", "title": "Impersonal greeting", "severity": 1, "headline": "an impersonal greeting",
            "finding": f"It opens with a generic greeting (\u201c{g}\u201d) rather than your name.",
            "evidence": [], "why": ("Organisations that hold an account with you usually address you by name. Generic "
                                    "greetings suggest one message sent to thousands of people."),
            "action": "Treat generic greetings as a prompt to double-check who really sent the message.",
        })
    if a["signoff"]:
        s = re.sub(r"\s+", " ", a["signoff"].group(0))
        flags.append({
            "key": "signoff", "title": "Team/department sign-off", "severity": 1, "headline": "a team/department sign-off",
            "finding": f"It is signed off by a team or department (\u201c{s}\u201d) rather than an individual you can contact directly.",
            "evidence": [], "why": ("Scammers avoid naming a real individual who could be checked or contacted. "
                                    "Many genuine emails name a sender and give a way to reach them."),
            "action": "Look for a named contact and verify that person or department through an independent channel.",
        })
    if a["exclamations"] >= 3 or a["upper_ratio"] > 0.25:
        flags.append({
            "key": "tone", "title": "Alarmist formatting", "severity": 1, "headline": "alarmist formatting",
            "finding": (f"It uses {a['exclamations']} exclamation mark(s) and "
                        f"{a['upper_ratio']:.0%} of its letters are capitals."),
            "evidence": [], "why": "Heavy capitals and exclamation marks are used to grab attention and raise anxiety.",
            "action": "Calm, unemotional wording is typical of genuine notices; treat shouty emails with caution.",
        })

    flags.sort(key=lambda f: -f["severity"])
    return flags


def build_reassuring(a, flags):
    keys = {f["key"] for f in flags}
    signs = []
    if a["personal_greeting"]:
        signs.append(f"It addresses you by name (\u201c{a['personal_greeting'].group(0)}\u201d) - though attackers "
                     "can personalise messages too, so this alone is not proof.")
    if not a["links"]:
        signs.append("It contains no links to click.")
    elif all(l["official"] for l in a["links"]):
        signs.append("Every link points to the organisation's official domain.")
    elif "links" not in keys and "brand" not in keys:
        signs.append("The links show no obvious tricks (still hover over them before clicking).")
    if not ({"sensitive", "money"} & keys):
        signs.append("It does not ask for passwords, card details or payments.")
    if not ({"urgency", "threat"} & keys):
        signs.append("It does not pressure you with deadlines or threats.")
    return signs


def build_advice(flags, phishing):
    advice, seen = [], set()
    for f in flags:
        if f["action"] not in seen:
            seen.add(f["action"])
            advice.append(f["action"])
        if len(advice) >= 4:
            break
    if phishing:
        advice.append("If you have already clicked or typed details in: change that password straight away, turn on "
                      "multi-factor authentication, tell the real organisation, and report the email to your IT or "
                      "security team (or your country's scam-reporting service).")
    else:
        advice.append("Even for emails that look genuine, verify unexpected requests with the sender through a "
                      "separate channel before acting.")
    return advice


def build_summary(prediction, conf_pct, conf_label, flags, signs, a):
    top = [f["headline"] for f in flags[:3]]
    if prediction == "Phishing":
        text = f"This email looks like phishing (confidence {conf_pct}%, {conf_label})."
        if top:
            text += f" The most telling signs are {_join(top)}."
        return text
    text = f"This email looks legitimate (confidence {conf_pct}%, {conf_label})."
    if flags:
        text += f" Still, a few things are worth checking: {_join(top)}."
    if len(flags) >= 3 or any(f["severity"] >= 3 for f in flags):
        text += (" The model leans legitimate, but several red flags are present, so verify through a trusted "
                 "channel before acting on it.")
    return text


# --------------------------------------------------------------------------
# 6. The engine (model + feedback)
# --------------------------------------------------------------------------
class FeedbackEngine:
    def __init__(self, model, explainer, vectorizer, scaler, feature_cols=None, threshold=0.5):
        self.model, self.explainer = model, explainer
        self.vectorizer, self.scaler = vectorizer, scaler
        self.feature_cols = feature_cols or FEATURE_COLS
        self.threshold = threshold
        self.feature_names = vectorizer.get_feature_names_out()
        self.n_text = len(self.feature_names)

    def _matrix(self, raw_text, feats):
        x_text = self.vectorizer.transform([clean_text(raw_text)])
        x_struct = self.scaler.transform(pd.DataFrame([feats])[self.feature_cols])
        return hstack([x_text, csr_matrix(x_struct)]).tocsr()

    def _model_terms(self, X, k_pos=5, k_neg=4):
        """Phrases in THIS email that pushed the (logistic regression) model towards each verdict."""
        row = X[:, : self.n_text].tocoo()
        coefs = self.explainer.coef_[0][: self.n_text]
        contrib = sorted(((self.feature_names[j], v * coefs[j]) for j, v in zip(row.col, row.data)),
                         key=lambda t: t[1])

        def pick(items, k):
            items = items[:12]
            keep = [t for t in items if not any(t[0] != o[0] and f" {t[0]} " in f" {o[0]} " for o in items)]
            return keep[:k]

        pos = pick(sorted([c for c in contrib if c[1] > 0], key=lambda t: -t[1]), k_pos)
        neg = pick([c for c in contrib if c[1] < 0], k_neg)
        top = max([abs(c[1]) for c in pos + neg] or [1])
        fmt = lambda lst: [{"term": TERM_DISPLAY.get(t, t), "strength": _strength(v, top)} for t, v in lst]
        return {"phishing": fmt(pos), "legitimate": fmt(neg)}

    def analyse(self, raw_text):
        a = analyse_email(raw_text)
        feats = features_from_analysis(a)
        X = self._matrix(raw_text, feats)
        p = float(self.model.predict_proba(X)[0][1])
        prediction = "Phishing" if p >= self.threshold else "Legitimate"
        conf = p if prediction == "Phishing" else 1 - p
        conf_label = "high" if conf >= 0.85 else "moderate" if conf >= 0.65 else "borderline"

        flags = build_flags(a)
        signs = build_reassuring(a, flags)
        phishing = prediction == "Phishing"
        extra = []
        if phishing:
            polished = a["exclamations"] < 2 and a["upper_ratio"] < 0.12 and len(a["plain"]) > 150
            if polished:
                extra.append("The writing is calm and polished. Perfect grammar is no longer a sign of a genuine "
                             "email - AI tools can produce flawless, personalised phishing at scale, so judge the "
                             "links, the request and the sender instead.")
            if a["personal_greeting"]:
                extra.append(f"It addresses you by name (\u201c{a['personal_greeting'].group(0)}\u201d). Personal "
                             "details are easy to scrape or generate, so a name is not proof of authenticity.")
        return {
            "prediction": prediction,
            "probability_phishing": round(p, 4),
            "confidence": round(conf, 4),
            "confidence_label": conf_label,
            "summary": build_summary(prediction, round(conf * 100), conf_label, flags, signs, a),
            "red_flags": flags,
            "reassuring_signs": signs,
            "ai_era_notes": extra,
            "model_terms": self._model_terms(X),
            "advice": build_advice(flags, phishing),
            "links": [{"url": l["url"], "domain": l["domain"], "issues": [m for _, m in l["issues"]]}
                      for l in a["links"]],
        }


def load_engine(path="ica_model_bundle.pkl"):
    import joblib
    b = joblib.load(path)
    return FeedbackEngine(b["model"], b["explainer"], b["vectorizer"], b["scaler"], b["feature_cols"])


# --------------------------------------------------------------------------
# 7. Markdown report (for notebooks / quick display)
# --------------------------------------------------------------------------
def md_escape(text):
    return re.sub(r"([\\`*_{}\[\]<>#$|])", r"\\\1", str(text))


def render_markdown(r):
    phishing = r["prediction"] == "Phishing"
    out = [f"### Verdict: {'Likely PHISHING' if phishing else 'Likely LEGITIMATE'} "
           f"({round(r['confidence'] * 100)}% confidence, {r['confidence_label']})", "",
           md_escape(r["summary"]), ""]

    mt = r["model_terms"]
    if mt["phishing"] or mt["legitimate"]:
        out.append("**What the model picked up on in this email**")
        if mt["phishing"]:
            out.append("- Wording it associates with phishing: " +
                       ", ".join(f"`{t['term']}` ({t['strength']})" for t in mt["phishing"]))
        if mt["legitimate"]:
            out.append("- Wording it associates with genuine email: " +
                       ", ".join(f"`{t['term']}` ({t['strength']})" for t in mt["legitimate"]))
        out.append("")

    flags = r["red_flags"]
    if flags:
        out.append(f"#### {'Red flags found' if phishing else 'Points worth a second look'} ({len(flags)})")
        for i, f in enumerate(flags, 1):
            sev = {4: "HIGH", 3: "HIGH", 2: "MEDIUM", 1: "LOW"}[f["severity"]]
            tag = f" - {f['principle']}" if f.get("principle") else ""
            out.append(f"**{i}. {f['title']}** ({sev}{tag})")
            out.append(f"- **What we found:** {md_escape(f['finding'])}")
            if f["evidence"]:
                out.append("- **In your email:**")
                out += [f"  > {md_escape(e)}" for e in f["evidence"]]
            out.append(f"- **Why it matters:** {md_escape(f['why'])}")
            out.append(f"- **What to do:** {md_escape(f['action'])}")
            out.append("")
    else:
        out += ["#### Red flags", "No strong phishing indicators were found in the wording or links.", ""]

    if r["ai_era_notes"]:
        out.append("#### Don't be reassured by...")
        out += [f"- {md_escape(n)}" for n in r["ai_era_notes"]]
        out.append("")
    if r["reassuring_signs"] and not phishing:
        out.append("#### Things that look normal")
        out += [f"- {md_escape(s)}" for s in r["reassuring_signs"]]
        out.append("")

    out.append("#### What you should do")
    out += [f"{i}. {md_escape(a)}" for i, a in enumerate(r["advice"], 1)]
    return "\n".join(out)
