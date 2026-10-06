"use client";

import { useEffect, useRef, useState } from "react";
import { submitAnswer, type Email } from "./actions";

export default function Quiz({ initialEmail }: { initialEmail: Email }) {
  const [email, setEmail] = useState(initialEmail);
  const [result, setResult] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const shownAt = useRef(0);

  useEffect(() => {
    shownAt.current = performance.now();
  }, [email]);

  async function answer(userAnswer: 0 | 1) {
    const responseTime = (performance.now() - shownAt.current) / 1000;
    setPending(true);
    try {
      const { correct, next } = await submitAnswer(email.email_id, userAnswer, responseTime);
      setResult(correct ? "Correct" : "Wrong");
      setEmail(next);
    } catch (e) {
      setResult(`Error: ${(e as Error).message}`);
    } finally {
      setPending(false);
    }
  }

  return (
    <main>
      <h1>Is this phishing email?</h1>
      {result && <p>{result}</p>}
      <p>From: {email.sender}</p>
      <h2>{email.subject}</h2>
      <p style={{ whiteSpace: "pre-wrap" }}>{email.body}</p>
      <p><button disabled={pending} onClick={() => answer(0)}>
        Fake
      </button></p>
      <p><button disabled={pending} onClick={() => answer(1)}>
        Real
      </button></p>
    </main>
  );
}
