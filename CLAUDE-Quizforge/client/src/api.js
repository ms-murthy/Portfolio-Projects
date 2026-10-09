// Asks our Express server for a quiz. Returns the list of questions.
export async function fetchQuiz({ topic, difficulty }) {
  const response = await fetch("/api/quiz", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic, difficulty, count: 10 }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data.questions;
}
