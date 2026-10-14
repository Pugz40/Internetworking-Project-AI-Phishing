"""
api.py - small web service that gives the website its per-email feedback.

Run locally:   uvicorn api:app --port 8000
Then set FEEDBACK_API_URL=http://localhost:8000 in the website's .dev.vars
"""
import os
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from ica_feedback import analyse_email, load_engine

HERE = os.path.dirname(os.path.abspath(__file__))
engine = load_engine(os.path.join(HERE, "ica_model_bundle.pkl"))
API_KEY = os.environ.get("FEEDBACK_API_KEY")  # optional shared secret

app = FastAPI(title="ICA feedback")


class FeedbackRequest(BaseModel):
    text: str = Field(..., max_length=30000)
    # Ground truth from the quiz database. True = the email really is phishing.
    # The feedback is written to match this, never to contradict it.
    is_phishing: Optional[bool] = None


def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1] if items else ""


def _summary(is_phishing, flags):
    top = [f["headline"] for f in flags[:3]]
    if is_phishing:
        if top:
            return f"This email is phishing. The most telling signs are {_join(top)}."
        return ("This email is phishing, but it is a subtle one: it avoids the obvious warning signs. "
                "When nothing looks wrong, check the sender's real address and confirm any request "
                "through a channel you already trust.")
    if top:
        return (f"This email is legitimate. A few details can look suspicious at first ({_join(top)}), "
                "but on their own they do not make an email phishing. Always weigh them against who sent "
                "it and whether you were expecting it.")
    return "This email is legitimate. Nothing in the wording or links points to a scam."


# Short one-line tips shown in italics after each finding
TIPS = {
    "sensitive": "Never send passwords, PINs or card details by email.",
    "urgency": "Don't be rushed - real organisations rarely demand action within hours.",
    "threat": "Don't click through to 'fix' it - log in to the real service directly and check.",
    "money": "Verify payment requests through a separate channel before sending money.",
    "lure": "If you didn't enter or apply for it, ignore it.",
    "pretext": "If you weren't expecting a file, voicemail or delivery, don't open it.",
    "action": "Don't click links or open attachments you weren't expecting.",
    "authority": "Check the sender's real address and confirm the request another way.",
    "secrecy": "Being told to keep quiet is meant to stop you checking with others.",
    "links": "Don't click it - type the organisation's address yourself instead.",
    "insecure": "Never enter passwords or payment details on an http:// page.",
    "brand": "Check the brand's own website or app directly instead.",
    "greeting": "A generic greeting suggests one message sent to thousands of people.",
    "signoff": "Look for a named contact and verify them independently.",
    "tone": "Shouting capitals and exclamation marks are meant to raise anxiety.",
}


def _quoted(items):
    return _join([f"\u201c{i}\u201d" for i in items])


def _phrases(a, key, limit=3):
    seen, out = set(), []
    for phrase, _s, _e in a["hits"].get(key, []):
        k = phrase.lower()
        if k not in seen:
            seen.add(k)
            out.append(k)
        if len(out) >= limit:
            break
    return out


def _bullets(truth, flags, r, a, notes):
    """Compact feedback: bold label, what was found in THIS email, short italic tip."""
    m = {"verdict": r["prediction"], "confidence": r["confidence"],
         "agrees": (r["prediction"] == "Phishing") == truth}
    word = "phishing" if truth else "legitimate"
    conf = f" ({round(m['confidence'] * 100)}% model confidence)" if m["agrees"] else ""
    out = [{"label": "Verdict", "text": f"{word}{conf}."}]

    bad_links = [l for l in r["links"] if l["issues"]]
    for f in flags[:5]:
        key = f["key"]
        if key == "links" and bad_links:
            l = bad_links[0]
            text = f"{_quoted([l['domain']])} {l['issues'][0]}."
        elif key in a["hits"] and _phrases(a, key):
            text = f"Uses {_quoted(_phrases(a, key))}."
        else:
            text = f["finding"]
        out.append({"label": f["title"], "text": text, "tip": TIPS.get(key)})

    terms = r["model_terms"]["phishing" if truth else "legitimate"] if m["agrees"] else []
    if terms:
        out.append({"label": "Wording the model linked to " + ("phishing" if truth else "genuine email"),
                    "terms": [t["term"] for t in terms]})

    if truth:
        for n in notes:
            label = ("Polished writing isn't proof of safety" if n.startswith("The writing")
                     else "A personal name isn't proof either")
            short = ("AI can write flawless, personalised phishing, so judge the links, the request and "
                     "the sender instead." if n.startswith("The writing")
                     else "Names are easy to scrape or generate.")
            out.append({"label": label, "text": short})
        out.append({"label": "If you already clicked or entered details",
                    "text": "change that password, turn on multi-factor authentication and tell the real "
                            "organisation."})
    else:
        signs = r["reassuring_signs"][:2]
        if signs:
            out.append({"label": "Looks normal", "text": " ".join(signs)})
        out.append({"label": "Still",
                    "text": "verify unexpected requests with the sender through a separate channel before acting."})
    return out


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/feedback")
def feedback(req: FeedbackRequest, x_api_key: Optional[str] = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="bad api key")
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="empty email")

    r = engine.analyse(req.text)
    model_says_phishing = r["prediction"] == "Phishing"
    truth = req.is_phishing if req.is_phishing is not None else model_says_phishing

    flags = []
    for f in r["red_flags"]:
        ev = f["evidence"] if f["key"] in ("links", "insecure") else f["evidence"][:2]
        flags.append({**f, "evidence": ev})

    # AI-era note only makes sense for a genuinely phishing email
    a = analyse_email(req.text)
    notes = []
    if truth:
        if a["exclamations"] < 2 and a["upper_ratio"] < 0.12 and len(a["plain"]) > 150:
            notes.append("The writing is calm and polished. Perfect grammar is no longer a sign of a genuine "
                         "email, because AI tools can write flawless phishing at scale. Judge the links, the "
                         "request and the sender instead.")
        if a["personal_greeting"]:
            notes.append(f"It addresses you by name (\u201c{a['personal_greeting'].group(0)}\u201d). Names are "
                         "easy to scrape or generate, so a name is not proof of authenticity.")

    from ica_feedback import build_advice
    return {
        "is_phishing": truth,
        "summary": _summary(truth, flags),
        "red_flags": flags,
        "reassuring_signs": r["reassuring_signs"] if not truth else [],
        "ai_era_notes": notes,
        "advice": build_advice(flags, truth),
        "bullets": _bullets(truth, flags, r, a, notes),
        "model": {"verdict": r["prediction"], "confidence": r["confidence"],
                  "agrees": model_says_phishing == truth},
    }
