import { getRandomEmail } from "../actions";
import Quiz from "../quiz";

export const dynamic = "force-dynamic";

export default async function TrainingQuizPage() {
  const email = await getRandomEmail();

  return <Quiz initialEmail={email} mode="training" />;
}