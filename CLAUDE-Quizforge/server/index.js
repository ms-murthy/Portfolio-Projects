import path from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";
import express from "express";
import Anthropic from "@anthropic-ai/sdk";

// The .env file lives in the project root, one folder above server/.
const here = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(here, "..", ".env") });

const PORT = process.env.PORT || 4000;
const MODEL = process.env.CLAUDE_MODEL || "claude-sonnet-5-5";

if (!process.env.ANTHROPIC_API_KEY) {
  console.error("\nMissing ANTHROPIC_API_KEY. Copy .env.example to .env and add your key.\n");
  process.exit(1);
}

const client = new Anthropic(); // reads ANTHROPIC_API_KEY from the environment
const app = express();
app.use(express.json());
// After `npm run build`, Express serves the finished React app from client/dist.
app.use(express.static(path.join(here, "..", "client", "dist")));

const DIFFICULTY_HINTS = {
  easy: "Well-known facts that most people would recognise.",
  medium: "Familiar territory that needs some real knowledge.",
  hard: "Detailed questions aimed at true enthusiasts.",
};

function buildPrompt(topic, difficulty, count) {
  return `Write a multiple-choice quiz.

Topic: ${topic}
Difficulty: ${difficulty} - ${DIFFICULTY_HINTS[difficulty]}
Number of questions: ${count}

Rules:
- Each question has exactly 4 options and exactly one correct answer.
- Vary the position of the correct answer.
- Give a short explanation (1-2 sentences) of why the answer is correct.
- Only include facts you are confident are accurate.

Reply with ONLY valid JSON, no markdown, in this shape:
{"questions":[{"question":"...","options":["...","...","...","..."],"correctIndex":0,"explanation":"..."}]}`;
}

// Pull the JSON out of the reply and check it has the shape we expect.
function parseQuiz(text) {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start === -1 || end === -1) throw new Error("No JSON found in reply");
  const data = JSON.parse(text.slice(start, end + 1));
  if (!Array.isArray(data.questions) || data.questions.length === 0) {
    throw new Error("No questions in reply");
  }
  for (const q of data.questions) {
    const ok =
      typeof q.question === "string" &&
      Array.isArray(q.options) &&
      q.options.length === 4 &&
      Number.isInteger(q.correctIndex) &&
      q.correctIndex >= 0 &&
      q.correctIndex < 4 &&
      typeof q.explanation === "string";
    if (!ok) throw new Error("A question had the wrong format");
  }
  return data.questions;
}

app.post("/api/quiz", async (req, res) => {
  const topic = String(req.body.topic || "").trim().slice(0, 200);
  const difficulty = Object.hasOwn(DIFFICULTY_HINTS, req.body.difficulty)
    ? req.body.difficulty
    : "medium";
  const count = [5, 10, 15].includes(Number(req.body.count)) ? Number(req.body.count) : 10;

  if (!topic) return res.status(400).json({ error: "Please enter a topic." });

  try {
    const message = await client.messages.create({
      model: MODEL,
      max_tokens: 6000,
      messages: [{ role: "user", content: buildPrompt(topic, difficulty, count) }],
    });
    const text = message.content
      .filter((block) => block.type === "text")
      .map((block) => block.text)
      .join("");
    res.json({ topic, difficulty, questions: parseQuiz(text) });
  } catch (err) {
    console.error("Quiz generation failed:", err.message);
    res.status(500).json({ error: friendlyError(err) });
  }
});

// Turn an API failure into a message a user can act on.
// (The full technical error is still printed in the server terminal above.)
function friendlyError(err) {
  if (err.status === 401 || err.status === 403) {
    return "The Anthropic API key is missing or invalid. Check the key in your .env file, then restart the server.";
  }
  if (err.status === 400 && /credit balance/i.test(err.message)) {
    return "Your Anthropic account is out of credits. Add credits in the Anthropic Console, then try again.";
  }
  if (err.status === 404) {
    return "The AI model name was not found. Check CLAUDE_MODEL in your .env file.";
  }
  if (err.status === 429) {
    return "Too many requests right now. Wait a moment and try again.";
  }
  if (err.status >= 500) {
    return "The AI service is busy or having problems. Please try again in a minute.";
  }
  if (err.status === undefined && /ENOTFOUND|ECONNREFUSED|ETIMEDOUT|fetch failed|Connection error/i.test(err.message)) {
    return "Could not reach the Anthropic API. Check your internet connection.";
  }
  // No status code: the reply arrived but was not a valid quiz.
  return "The AI sent back a quiz in an unexpected format. Please try again.";
}

app.listen(PORT, () => console.log(`Quizforge running at http://localhost:${PORT}`));
