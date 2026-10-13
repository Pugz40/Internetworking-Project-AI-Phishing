
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const TOTAL_QUESTIONS = 5;

export default function ResultsPage() {
  const [score, setScore] = useState<number | null>(null);

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
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center bg-slate-50 px-4 py-8">      <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-12">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50 text-3xl">
          🤖
        </div>

        <p className="mt-6 text-sm font-semibold uppercase tracking-widest text-emerald-700">
          Assessment complete
        </p>

        <h1 className="mt-3 text-3xl font-bold text-slate-900">
          Your Results
        </h1>

        {score === null ? (
          <>
            <p className="mt-4 leading-7 text-slate-600">
              No final assessment score was found in this browser
              session. Please complete the assessment first.
            </p>

            <Link
              href="/final-quiz"
              className="mt-7 inline-flex min-h-12 items-center justify-center rounded-xl bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700"
            >
              Go to final assessment
            </Link>
          </>
        ) : (
          <>
            {score >= 4 ? (
                <p className="mt-4 text-slate-600">
              Congratulations! You scored very highly.
            </p>
            ) : (
                <p className="mt-4 text-slate-600">
              You may want to review the learning guide and try again.
            </p>
            )}

            <div className="my-8 rounded-2xl bg-slate-50 p-8">
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

            <p className="text-sm leading-6 text-slate-600">
              Thank you for participating.
            </p>
          </>
        )}
        
      </div>


      
      <footer className="mt-8 text-center text-[10px] text-slate-500">
        <p>Improving Cybersecurity Awareness</p>
        <p className="mt-1">A simulation based approach to AI phishing awareness</p>
        <p className="mt-1">An educational research project by Angelina, Brendan, Dean, Dev, Emilie and Jerome</p>

        </footer>

      
    </main>
  );
}
