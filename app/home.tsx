
import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-12 sm:py-20">
      <div className="mx-auto flex min-h-[75vh] max-w-4xl flex-col items-center justify-center">
        {/* Brand */}
        <header className="mb-10 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="h-7 w-7"
              aria-hidden="true"
            >
              <path
                d="M12 3 4.5 6v5.5c0 4.5 3.1 7.6 7.5 9.5 4.4-1.9 7.5-5 7.5-9.5V6L12 3Z"
                strokeLinejoin="round"
              />
              <path
                d="m9 12 2 2 4-4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          <div>
            <p className="text-lg font-bold tracking-tight text-slate-900">
              Improving Cybersecurity Awareness
            </p>
            <p className="text-sm text-slate-500">
              A simulation based approach to AI phishing awareness
            </p>
          </div>
        </header>

        {/* Welcome card */}
        <section className="w-full rounded-3xl border border-slate-200 bg-white px-6 py-10 text-center shadow-sm sm:px-12 sm:py-14">
          <span className="inline-flex items-center rounded-full border border-blue-100 bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700">
            Training & Assessment
          </span>

          <h1 className="mx-auto mt-6 max-w-2xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Think before you click.
          </h1>

          <p className="mx-auto mt-5 max-w-xl text-base leading-7 text-slate-600 sm:text-lg">
            Learn to recognise phishing attempts by examining email
            messages, spotting suspicious details, and deciding which
            messages you can trust.
          </p>

          {/* What to expect */}
          <div className="mx-auto mt-10 grid max-w-2xl gap-4 text-left sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-700">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  className="h-5 w-5"
                  aria-hidden="true"
                >
                  <rect x="3" y="5" width="18" height="14" rx="2" />
                  <path d="m4 7 8 6 8-6" />
                </svg>
              </div>
              <h2 className="font-semibold text-slate-900">
                Review emails
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Inspect the sender, subject and message content.
              </p>
            </div>

            <div className="rounded-2xl bg-slate-50 p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-700">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  className="h-5 w-5"
                  aria-hidden="true"
                >
                  <circle cx="12" cy="12" r="9" />
                  <path
                    d="m9 12 2 2 4-4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <h2 className="font-semibold text-slate-900">
                Make a choice
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Decide whether each message is phishing or legitimate.
              </p>
            </div>

            <div className="rounded-2xl bg-slate-50 p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-700">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  className="h-5 w-5"
                  aria-hidden="true"
                >
                  <circle cx="12" cy="12" r="9" />
                  <path
                    d="M12 11v5m0-8h.01"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <h2 className="font-semibold text-slate-900">
                Learn from feedback
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Receive feedback on your answers and apply them to the assessment.
              </p>
            </div>
          </div>

          {/* Assessment details */}
          <div className="mx-auto mt-8 flex max-w-md flex-wrap items-center justify-center gap-x-6 gap-y-3 text-sm text-slate-500">
            <span className="flex items-center gap-2">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                className="h-4 w-4"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="9" />
                <path d="M12 7v5l3 2" strokeLinecap="round" />
              </svg>
              About 10–15 minutes
            </span>
            <span>5 emails per session</span>
            <span>Training and Final Assessment</span>
          </div>

          {/* Start button */}
          <Link
            href="/quiz"
            className="mt-9 inline-flex min-h-14 w-full max-w-sm items-center justify-center gap-3 rounded-xl bg-blue-600 px-8 py-4 font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Start training
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="h-5 w-5"
              aria-hidden="true"
            >
              <path
                d="M5 12h14m-7-7 7 7-7 7"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </Link>

          <p className="mt-4 text-xs leading-5 text-slate-500">
          Phishing Awareness Simulator · Educational research project
          </p>
        </section>

        <footer className="mt-8 text-center text-xs leading-5 text-slate-500">
          An educational research project by Angelina, Brendan, Dean, Dev, Emilie and Jerome
        </footer>
      </div>
    </main>
  );
}
