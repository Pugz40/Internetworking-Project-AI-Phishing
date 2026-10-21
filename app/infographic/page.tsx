
import Link from "next/link";

const tips = [
  {
    number: "01",
    title: "Check the sender",
    description:
      "Inspect the full email address and domain. Look for misspellings, unusual domains, and addresses that imitate trusted organisations.",
  },
  {
    number: "02",
    title: "Watch for urgency",
    description:
      "Be cautious of threats, unexpected account suspensions, and pressure to act immediately.",
  },
  {
    number: "03",
    title: "Inspect links",
    description:
      "Check where a link leads before opening it. A familiar display name or button does not guarantee a safe destination.",
  },
  {
    number: "04",
    title: "Question sensitive requests",
    description:
      "Treat unexpected requests for passwords, payment details, verification codes, or money with caution.",
  },
  {
    number: "05",
    title: "Look for inconsistencies",
    description:
      "Consider whether the message matches the context, expected communication, and usual process of the organisation.",
  },
  {
    number: "06",
    title: "Double check everything",
    description:
      "If you're unsure about an email, make sure you double check everything. AI-assisted analysis can highlight suspicious wording, links, and sender details, but always verify the evidence yourself.",
  },
];

export default function InfographicPage() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 sm:py-14">
      <div className="mx-auto max-w-4xl">
        <header className="rounded-2xl bg-slate-900 p-8 text-white sm:p-12">
          <p className="text-sm font-semibold uppercase tracking-widest text-blue-300">
            Your learning guide
          </p>

          <h1 className="mt-3 text-3xl font-bold sm:text-4xl">
            Pause. Check. Verify.
          </h1>

          <p className="mt-4 max-w-2xl leading-7 text-slate-300">
            Phishing emails can look convincing, even when they
            contain warning signs. Use these checks before trusting
            a message or acting on a request.
          </p>
        </header>

        <section className="mt-6 grid gap-4 sm:grid-cols-2">
          {tips.map((tip) => (
            <article
              key={tip.number}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <p className="text-sm font-bold text-blue-600">
                CHECK {tip.number}
              </p>

              <h2 className="mt-3 text-xl font-bold text-slate-900">
                {tip.title}
              </h2>

              <p className="mt-3 text-sm leading-7 text-slate-600">
                {tip.description}
              </p>
            </article>
          ))}
        </section>

        <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-6">
          <h2 className="font-bold text-amber-950">
            Remember
          </h2>
          <p className="mt-2 text-sm leading-7 text-amber-900">
            Good grammar, professional branding, and a familiar
            name do not prove an email is legitimate. When unsure,
            verify through a separate, trusted channel.
          </p>
        </div>

        <div className="mt-8 text-center">
          <p className="mb-4 text-sm text-slate-600">
            Apply these checks to five new emails.
          </p>

          <Link
            href="/final-quiz"
            className="inline-flex min-h-12 items-center justify-center rounded-xl bg-blue-600 px-7 py-3 font-semibold text-white transition hover:bg-blue-700"
          >
            Begin final assessment →
          </Link>
        </div>
      </div>
    </main>
  );
}
