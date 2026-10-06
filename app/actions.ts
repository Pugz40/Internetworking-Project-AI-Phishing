"use server";

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
    .from("human_emails")
    .select("email_id", { count: "exact", head: true });
  if (countError) throw new Error(countError.message);
  if (!count) throw new Error("human_emails is empty");

  const offset = Math.floor(Math.random() * count);
  const { data, error } = await supabase
    .from("human_emails")
    .select("email_id, sender, subject, body")
    .order("email_id")
    .range(offset, offset)
    .single();
  if (error) throw new Error(error.message);

  return data;
}

// userAnswer: 0 = fake, 1 = real. responseTime in seconds.
export async function submitAnswer(emailId: number, userAnswer: 0 | 1, responseTime: number) {
  const supabase = getSupabase();

  const { data: email, error: emailError } = await supabase
    .from("human_emails")
    .select("label")
    .eq("email_id", emailId)
    .single();
  if (emailError) throw new Error(emailError.message);

  // human_emails.label is 1 = phishing; convert to answer scale (0 = fake, 1 = real)
  const actualLabel = 1 - Number(email.label);
  const correct = userAnswer === actualLabel ? 1 : 0;

  // Draft: max+1 can collide if two answers are submitted at the same moment
  const { data: last, error: lastError } = await supabase
    .from("quiz_sessions")
    .select("id")
    .order("id", { ascending: false })
    .limit(1);
  if (lastError) throw new Error(lastError.message);
  const id = last.length ? last[0].id + 1 : 0;

  const { error: sessionError } = await supabase.from("quiz_sessions").insert({ id });
  if (sessionError) throw new Error(sessionError.message);

  const { error: resultError } = await supabase.from("user_results").insert({
    id,
    session_id: id,
    email_id: emailId,
    email_source: "human",
    actual_label: actualLabel,
    user_answer: userAnswer,
    correct,
    answered_at: new Date().toISOString(),
    response_time: responseTime,
  });
  if (resultError) throw new Error(resultError.message);

  return { correct, next: await getRandomEmail() };
}
