
"use client";
import { useRouter } from "next/navigation";


import { useEffect, useRef, useState } from "react";
import { getFeedback, submitAnswer, type Email, type Feedback } from "./actions";
import FeedbackPanel, { type FeedbackState } from "./feedback-panel";
type QuizMode = "training" | "final";
const TOTAL_QUESTIONS = 5;

type AnswerResult = {
  correct: number;
  next: Email;
};

export default function Quiz({
  initialEmail,
  mode,
}: {
  initialEmail: Email;
  mode: QuizMode;
}) {
  const router = useRouter();
  const [email, setEmail] = useState(initialEmail);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [feedbackState, setFeedbackState] = useState<FeedbackState>("loading");

  const shownAt = useRef(0);
  const feedbackRequest = useRef(0); // ignore replies that arrive after moving to the next email

  useEffect(() => {
    shownAt.current = performance.now();
  }, [email]);

  async function answer(userAnswer: 0 | 1) {
    if (pending || result) return;

    const responseTime =
      (performance.now() - shownAt.current) / 1000;

    setPending(true);
    setError(null);

    try {
      const response = await submitAnswer(
        email.email_id,
        userAnswer,
        responseTime
      );

      setResult({
        correct: response.correct,
        next: response.next,
      });

      if (mode === "training") {
        const requestId = ++feedbackRequest.current;
        setFeedback(null);
        setFeedbackState("loading");
        getFeedback(email.email_id)
          .then((fb) => {
            if (requestId !== feedbackRequest.current) return;
            setFeedback(fb);
            setFeedbackState(fb ? "ready" : "failed");
          })
          .catch(() => {
            if (requestId !== feedbackRequest.current) return;
            setFeedbackState("failed");
          });
      }
    if (mode === "final") {
  setScore((currentScore) => currentScore + response.correct);
}
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setPending(false);
    }
  }

function continueQuiz() {
  if (!result) return;

  if (questionNumber >= TOTAL_QUESTIONS) {
    if (mode === "training") {
      router.push("/infographic");
    } else {
      sessionStorage.setItem("phishingFinalScore", String(score));
      router.push("/results");
    }

    return;
  }

  feedbackRequest.current++;
  setFeedback(null);
  setEmail(result.next);
  setQuestionNumber((current) => current + 1);
  setResult(null);
  setError(null);
}

  const progress = (questionNumber / TOTAL_QUESTIONS) * 100;

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 sm:py-12">
      <div className="mx-auto max-w-3xl">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                className="h-6 w-6"
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
          </div>
        </header>

        {/* Progress */}
        <section
          aria-label="Quiz progress"
          className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div className="mb-3 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-900">
                Email Awareness
              </p>
              <p className="mt-1 text-sm text-slate-500">
                Inspect each message before making your choice.
              </p>
            </div>

            <span className="shrink-0 rounded-full bg-blue-50 px-3 py-1.5 text-sm font-semibold text-blue-700">
              {questionNumber} of {TOTAL_QUESTIONS}
            </span>
          </div>

          <div
            className="h-2 overflow-hidden rounded-full bg-slate-100"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={TOTAL_QUESTIONS}
            aria-valuenow={questionNumber}
            aria-label="Current email"
          >
            <div
              className="h-full rounded-full bg-blue-600 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </section>

        {/* Email card */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4 sm:px-7">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Message inspection
                </p>
                <h1 className="mt-1 text-xl font-bold text-slate-900">
                  Is this email phishing?
                </h1>
              </div>

              <div className="hidden rounded-lg bg-slate-100 p-3 text-slate-600 sm:block">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  className="h-6 w-6"
                  aria-hidden="true"
                >
                  <rect x="3" y="5" width="18" height="14" rx="2" />
                  <path
                    d="m4 7 8 6 8-6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            </div>
          </div>

          <div className="p-5 sm:p-7">
            {/* Sender and subject */}
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  From
                </p>
                <p className="mt-1 break-words text-sm font-medium text-slate-800">
                  {email.sender}
                </p>
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Subject
                </p>
                <p className="mt-1 break-words text-base font-semibold text-slate-900">
                  {email.subject}
                </p>
              </div>
            </div>

            <div className="my-6 border-t border-slate-100" />

            
          {/* Email body */}
          <div className="h-64 overflow-y-auto rounded-xl bg-slate-50 p-5 sm:p-6">
            <p className="whitespace-pre-wrap break-words text-sm leading-7 text-slate-700">
              {email.body}
            </p>
          </div>


            {/* Instructions */}
            {mode === "training"  && (
            <div className="mt-6">
              <p className="text-sm font-semibold text-slate-900">
                What do you think?
              </p>
              <p className="mt-1 text-sm leading-6 text-slate-500">
                Consider the sender, subject, wording and any requests
                before deciding whether this message is genuine.
              </p>
            </div>
            )}

            {/* Answer buttons */}
            <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <button
                type="button"
                disabled={pending || result !== null}
                onClick={() => answer(0)}
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-rose-200 bg-white px-5 py-3 font-semibold text-rose-700 transition hover:border-rose-300 hover:bg-rose-50 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span aria-hidden="true">✕</span>
                Fake — phishing
              </button>

              <button
                type="button"
                disabled={pending || result !== null}
                onClick={() => answer(1)}
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-white px-5 py-3 font-semibold text-emerald-700 transition hover:border-emerald-300 hover:bg-emerald-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span aria-hidden="true">✓</span>
                Real — legitimate
              </button>
            </div>

            {/* Loading */}
            {pending && (
              <p
                role="status"
                className="mt-4 text-center text-sm text-slate-500"
              >
                Recording your answer...
              </p>
            )}

            {/* Error */}
            {error && (
              <div
                role="alert"
                className="mt-5 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800"
              >
                <p className="font-semibold">Unable to submit your answer</p>
                <p className="mt-1">{error}</p>
                <button
                  type="button"
                  onClick={() => setError(null)}
                  className="mt-2 font-semibold underline underline-offset-2"
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* Feedback */}
            {mode === "training" && result && (
              <div
                role="status"
                aria-live="polite"
                className={`mt-6 rounded-xl border p-5 ${
                  result.correct
                    ? "border-emerald-200 bg-emerald-50"
                    : "border-amber-200 bg-amber-50"
                }`}
              >
                <div className="flex items-start gap-3">
                  <span
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-bold ${
                      result.correct
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-amber-100 text-amber-700"
                    }`}
                    aria-hidden="true"
                  >
                    {result.correct ? "✓" : "!"}
                  </span>

                  <div className="flex-1">
                    <h2
                      className={`font-bold ${
                        result.correct
                          ? "text-emerald-900"
                          : "text-amber-900"
                      }`}
                    >
                      {result.correct ? "Correct!" : "Not quite."}
                    </h2>

                    <FeedbackPanel
                      correct={result.correct === 1}
                      state={feedbackState}
                      feedback={feedback}
                    />

                    <button
                      type="button"
                      onClick={continueQuiz}
                      className="mt-4 inline-flex min-h-11 items-center justify-center rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2"
                    >
                      {questionNumber >= TOTAL_QUESTIONS
                        ? "Finish training"
                        : "Next email"}
                      <span className="ml-2" aria-hidden="true">
                        →
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            )}
            {/* Final assessment navigation: no correctness feedback */}
{mode === "final" && result && (
  <div className="mt-6 flex justify-end">
    <button
      type="button"
      onClick={continueQuiz}
      className="inline-flex min-h-11 items-center justify-center rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2"
    >
      {questionNumber >= TOTAL_QUESTIONS
        ? "View results"
        : "Next email"}
      <span className="ml-2" aria-hidden="true">
        →
      </span>
    </button>
  </div>
)}
          </div>
        </section>

        <footer className="mt-6 text-center text-xs leading-5 text-slate-500">
          Training simulation only. Always verify suspicious messages
          through a trusted channel.
        </footer>
      </div>
    </main>
  );
}
