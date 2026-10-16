"use server";

import { env } from "cloudflare:workers";
import { getSupabase } from "../lib/supabase";

export type Email = {
  email_id: number;
  sender: string;
  subject: string;
  body: string;
};

export async function getRandomEmail(): Promise<Email> {
  const supabase = getSupabase();

  const { count, error: countError } = await supabase
    .from("ai_emails")
    .select("email_id", { count: "exact", head: true });
  if (countError) throw new Error(countError.message);
  if (!count) throw new Error("ai_emails is empty");

  const offset = Math.floor(Math.random() * count);
  const { data, error } = await supabase
    .from("ai_emails")
    .select("email_id, sender, subject, body")
    .order("email_id")
    .range(offset, offset)
    .single();
  if (error) throw new Error(error.message);

  return { ...data, sender: data.sender ?? "Unknown sender" };
}

// Draft: max+1 can collide if two rows are inserted at the same moment
async function nextId(table: "quiz_sessions" | "user_results"): Promise<number> {
  const { data, error } = await getSupabase()
    .from(table)
    .select("id")
    .order("id", { ascending: false })
    .limit(1);
  if (error) throw new Error(error.message);
  return data.length ? data[0].id + 1 : 0;
}

// Called once per browser tab visit (see app/session.ts)
export async function startSession(): Promise<number> {
  const id = await nextId("quiz_sessions");
  const { error } = await getSupabase().from("quiz_sessions").insert({ id });
  if (error) throw new Error(error.message);
  return id;
}

// userAnswer: 0 = fake, 1 = real. responseTime in seconds.
export async function submitAnswer(
  sessionId: number,
  emailId: number,
  userAnswer: 0 | 1,
  responseTime: number
) {
  const supabase = getSupabase();

  const { data: email, error: emailError } = await supabase
    .from("ai_emails")
    .select("label")
    .eq("email_id", emailId)
    .single();
  if (emailError) throw new Error(emailError.message);

  // ai_emails.label is 1 = phishing; convert to answer scale (0 = fake, 1 = real)
  const actualLabel = 1 - Number(email.label);
  const correct = userAnswer === actualLabel ? 1 : 0;

  const id = await nextId("user_results");

  const { error: resultError } = await supabase.from("user_results").insert({
    id,
    session_id: sessionId,
    email_id: emailId,
    email_source: "ai",
    actual_label: actualLabel,
    user_answer: userAnswer,
    correct,
    answered_at: new Date().toISOString(),
    response_time: responseTime,
  });
  if (resultError) throw new Error(resultError.message);

  return { correct, actualLabel, next: await getRandomEmail() };
}

export type FeedbackBullet = {
  label: string;
  text?: string;
  terms?: string[]; // words the model picked up on, shown in monospace
  tip?: string; // short italic advice
};

export type Feedback = {
  is_phishing: boolean;
  bullets: FeedbackBullet[];
};

// Asks the ICA feedback service (ica_export/api.py) to analyse this exact email.
// Returns null if the service is not configured or unreachable, so the quiz still works.
export async function getFeedback(emailId: number): Promise<Feedback | null> {
  const base = env.FEEDBACK_API_URL?.trim();
  if (!base) return null;

  try {
    const supabase = getSupabase();
    const { data: email, error } = await supabase
      .from("ai_emails")
      .select("subject, body, label")
      .eq("email_id", emailId)
      .single();
    if (error) return null;

    const res = await fetch(`${base.replace(/\/$/, "")}/feedback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(env.FEEDBACK_API_KEY ? { "x-api-key": env.FEEDBACK_API_KEY } : {}),
      },
      body: JSON.stringify({
        text: `${email.subject}\n\n${email.body}`,
        is_phishing: Number(email.label) === 1,
      }),
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) return null;
    return (await res.json()) as Feedback;
  } catch {
    return null;
  }
}
