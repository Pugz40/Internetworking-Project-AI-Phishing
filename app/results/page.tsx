
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getSessionResults, type SessionEmailResult } from "../actions";

const TOTAL_QUESTIONS = 5;
const SESSION_ID_KEY = "phishingSessionId";

export default function ResultsPage() {
  const [score, setScore] = useState<number | null>(null);
  const [emailResults, setEmailResults] = useState<SessionEmailResult[]>([]);
  const [loadingResults, setLoadingResults] = useState(true);
  const [resultsError, setResultsError] = useState<string | null>(null);

  useEffect(() => {
    const savedScore = sessionStorage.getItem("phishingFinalScore");

    if (savedScore !== null) {
      const parsedScore = Number(savedScore);

      if (
        Number.isInteger(parsedScore) &&
        parsedScore >= 0 &&
        parsedScore <= TOTAL_QUESTIONS
      ) {
        setScore(parsedScore);
      }
    }

    const savedSessionId = sessionStorage.getItem(SESSION_ID_KEY);

    if (savedSessionId === null) {
      setResultsError(
        "The session ID could not be found. Please complete the assessment in the same browser session."
      );
      setLoadingResults(false);
      return;
    }

    const sessionId = Number(savedSessionId);

    if (!Number.isSafeInteger(sessionId) || sessionId < 0) {
      setResultsError("The saved session ID is invalid.");
      setLoadingResults(false);
      return;
    }

    getSessionResults(sessionId, "final")
      .then(setEmailResults)
      .catch(() => {
        setResultsError("Unable to load your email results. Please try again.");
      })
      .finally(() => setLoadingResults(false));
  }, []);

  const classification = (answer: number) =>
    answer === 0 ? "Phishing" : "Legitimate";

  return (
    <main className="flex min-h-screen flex-col items-center bg-slate-50 px-4 py-8">
      <div className="w-full max-w-3xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm sm:p-12">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50 text-3xl">
          🤖
        </div>

        <p className="mt-6 text-center text-sm font-semibold uppercase tracking-widest text-emerald-700">
          Assessment complete
        </p>

        <h1 className="mt-3 text-center text-3xl font-bold text-slate-900">
          Your Results
        </h1>

        {score === null ? (
          <div className="text-center">
            <p className="mt-4 leading-7 text-slate-600">
              No final assessment score was found in this browser session.
              Please complete the assessment first.
            </p>
            <Link
              href="/final-quiz"
              className="mt-7 inline-flex min-h-12 items-center justify-center rounded-xl bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700"
            >
              Go to final assessment
            </Link>
          </div>
        ) : (
          <>
          <p className="mt-4 text-center text-slate-600">
          {score <= 1
            ? "Did you even try???"
            : score <= 3
            ? "Not bad! Review the learning guide and try again."
            : "Congratulations! You scored very highly!"}
          </p>

            <div className="my-8 rounded-2xl bg-slate-50 p-8 text-center">
              <p className="text-sm font-semibold text-slate-500">
                Correct answers
              </p>
              <p className="mt-2 text-5xl font-bold text-slate-900">
                {score} / {TOTAL_QUESTIONS}
              </p>
              <p className="mt-3 text-slate-600">
                {Math.round((score / TOTAL_QUESTIONS) * 100)}% correct
              </p>
            </div>
          </>
        )}

        <section className="mt-10">
          <h2 className="text-xl font-bold text-slate-900">
            Your Email Responses
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Review the emails you answered in the final assessment.
          </p>

          {loadingResults ? (
            <p className="mt-5 text-slate-600">Loading your email results...</p>
          ) : resultsError ? (
            <p className="mt-5 text-sm text-red-700">{resultsError}</p>
          ) : emailResults.length === 0 ? (
            <p className="mt-5 text-slate-600">
              No saved email responses were found for this session.
            </p>
          ) : (
            <div className="mt-5 space-y-4">
              {emailResults.map((result, index) => (
                <article
                  key={`${result.email_id}-${index}`}
                  className="rounded-xl border border-slate-200 p-5"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <h3 className="font-semibold text-slate-900">
                      {index + 1}. {result.subject}
                    </h3>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        result.correct === 1
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {result.correct === 1 ? "Correct" : "Incorrect"}
                    </span>
                  </div>

                  <p className="mt-2 text-sm text-slate-500">
                    From: {result.sender}
                  </p>

                  <div className="mt-4 space-y-2 text-sm">
                    <p className="text-slate-700">
                      <span className="font-semibold">Your answer:</span>{" "}
                      {classification(result.user_answer)}
                    </p>
                    <p className="text-slate-700">
                      <span className="font-semibold">Correct answer:</span>{" "}
                      {classification(result.actual_label)}
                    </p>
                    {result.response_time !== null && (
                      <p className="text-slate-500">
                        Response time: {result.response_time.toFixed(1)} seconds
                      </p>
                    )}
                  </div>

                  <details className="mt-4">
                    <summary className="cursor-pointer text-sm font-semibold text-blue-700 hover:text-blue-900">
                      View email content
                    </summary>
                    <div className="mt-3 rounded-lg bg-slate-50 p-4">
                      <p className="whitespace-pre-wrap break-words text-sm leading-6 text-slate-700">
                        {result.body}
                      </p>
                    </div>
                  </details>
                </article>
              ))}
            </div>
          )}
        </section>

        <div className="mt-10 border-t border-slate-200 pt-6 text-center">
          <p className="text-sm leading-6 text-slate-600">
            Thank you for participating! Please complete the survey below to
            help us improve this educational experience.
          </p>
          <a
            href="https://docs.google.com/forms/d/e/1FAIpQLSdr6GJh5AHlSsvXk7tTautGv3hga7R1pqWVdXwhkmABRpZJvg/viewform"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-block text-sm font-semibold text-blue-600 underline hover:text-blue-800"
          >
            Click here to take the survey
          </a>
        </div>
      </div>

      <footer className="mt-8 text-center text-[10px] text-slate-500">
        <p>Improving Cybersecurity Awareness</p>
        <p className="mt-1">
          A simulation based approach to AI phishing awareness
        </p>
        <p className="mt-1">
          An educational research project by Angelina, Brendan, Dean, Dev,
          Emilie and Jerome
        </p>
      </footer>
    </main>
  );
}
