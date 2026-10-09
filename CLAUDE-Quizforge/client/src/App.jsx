import { useCallback, useEffect, useState } from "react";
import { fetchQuiz } from "./api.js";
import { clearHistory, loadHistory, saveHistory } from "./history.js";
import SetupForm from "./components/SetupForm.jsx";
import Question from "./components/Question.jsx";
import Results from "./components/Results.jsx";

function initialTheme() {
  try {
    const saved = localStorage.getItem("quizforge-theme");
    if (saved) return saved;
  } catch {
    // localStorage unavailable - fall through to the system preference
  }
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  // Which screen is showing: "home" | "loading" | "quiz" | "results"
  const [screen, setScreen] = useState("home");
  const [quiz, setQuiz] = useState(null); // { topic, difficulty, timed, questions }
  const [current, setCurrent] = useState(0); // index of the current question
  const [answers, setAnswers] = useState([]); // picked option per question, -1 = timed out
  const [error, setError] = useState("");
  const [history, setHistory] = useState(loadHistory);
  const [theme, setTheme] = useState(initialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("quizforge-theme", theme);
    } catch {
      // ignore
    }
  }, [theme]);

  const score = quiz
    ? answers.filter((pick, i) => pick === quiz.questions[i].correctIndex).length
    : 0;

  async function startQuiz(settings) {
    setError("");
    setScreen("loading");
    try {
      const questions = await fetchQuiz(settings);
      setQuiz({ ...settings, questions });
      setCurrent(0);
      setAnswers([]);
      setScreen("quiz");
    } catch (err) {
      setError(err.message);
      setScreen("home");
    }
  }

  // Record an answer. Ignored if that question was already answered.
  const handleAnswer = useCallback((index, picked) => {
    setAnswers((prev) => {
      if (prev[index] !== undefined) return prev;
      const next = [...prev];
      next[index] = picked;
      return next;
    });
  }, []);

  function handleNext() {
    if (current < quiz.questions.length - 1) {
      setCurrent(current + 1);
      return;
    }
    setHistory(
      saveHistory({
        topic: quiz.topic,
        difficulty: quiz.difficulty,
        score,
        total: quiz.questions.length,
        date: Date.now(),
      })
    );
    setScreen("results");
  }

  return (
    <>
      <header className="topbar">
        <span className="logo">Quizforge</span>
        <button
          className="ghost"
          type="button"
          aria-label="Switch light or dark theme"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          Theme
        </button>
      </header>

      <main>
        {screen === "home" && (
          <SetupForm
            onStart={startQuiz}
            error={error}
            history={history}
            onClearHistory={() => setHistory(clearHistory())}
          />
        )}

        {screen === "loading" && (
          <section id="loading">
            <div className="spinner" aria-hidden="true" />
            <p>Writing your quiz...</p>
          </section>
        )}

        {screen === "quiz" && (
          <Question
            key={current}
            quiz={quiz}
            index={current}
            answers={answers}
            score={score}
            onAnswer={handleAnswer}
            onNext={handleNext}
          />
        )}

        {screen === "results" && (
          <Results
            quiz={quiz}
            answers={answers}
            score={score}
            onRetry={() => startQuiz({ topic: quiz.topic, difficulty: quiz.difficulty, timed: quiz.timed })}
            onNewTopic={() => setScreen("home")}
          />
        )}
      </main>
    </>
  );
}
