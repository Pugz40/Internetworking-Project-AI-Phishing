"use client";
import type { Feedback } from "./actions";

export type FeedbackState = "loading" | "ready" | "failed";

export default function FeedbackPanel({
  correct,
  state,
  feedback,
}: {
  correct: boolean;
  state: FeedbackState;
  feedback: Feedback | null;
}) {
  if (state === "loading") {
    return (
      <p className="mt-2 text-sm text-slate-600" role="status">
        Analysing this email...
      </p>
    );
  }

  // Feedback service unavailable: fall back to the generic message
  if (state === "failed" || !feedback) {
    return (
      <p className="mt-1 text-sm leading-6 text-slate-700">
        {correct
          ? "You identified this email correctly. Keep applying the same careful checks to the next message."
          : "Review the sender, subject, message wording and any links or requests. Look for details that support your decision."}
      </p>
    );
  }

  return (
    <div className="mt-2 text-sm leading-6 text-slate-700">
      <p className="font-bold text-slate-900">Feedback:</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5">
        {feedback.bullets.map((b, i) => (
          <li key={i} className="break-words">
            <span className="font-semibold text-slate-900">{b.label}:</span>
            {b.text && <> {b.text}</>}
            {b.terms && b.terms.length > 0 && (
              <>
                {" "}
                {b.terms.map((t, j) => (
                  <span key={t}>
                    <code className="rounded bg-white/70 px-1 font-mono text-xs">{t}</code>
                    {j < b.terms!.length - 1 ? ", " : "."}
                  </span>
                ))}
              </>
            )}
            {b.tip && <> <em className="text-slate-600">{b.tip}</em></>}
          </li>
        ))}
      </ul>
    </div>
  );
}
