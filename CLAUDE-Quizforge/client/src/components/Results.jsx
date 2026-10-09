import { useState } from "react";

function messageFor(ratio) {
  if (ratio === 1) return "Perfect score!";
  if (ratio >= 0.7) return "Great work.";
  if (ratio >= 0.4) return "Good effort. Review the misses below.";
  return "Tough one. Try again after reviewing.";
}

export default function Results({ quiz, answers, score, onRetry, onNewTopic }) {
  const total = quiz.questions.length;
  const [copied, setCopied] = useState(false);

  // Only the questions the user got wrong (or ran out of time on)
  const misses = quiz.questions
    .map((q, i) => ({ q, picked: answers[i] }))
    .filter(({ q, picked }) => picked !== q.correctIndex);

  // Plain-text version of everything shown on this screen
  function buildResultText() {
    const lines = [
      `Quizforge - ${quiz.topic} (${quiz.difficulty})`,
      `Score: ${score} out of ${total}`,
      messageFor(score / total),
    ];
    if (misses.length > 0) {
      lines.push("", "Questions to review:");
      misses.forEach(({ q, picked }, n) => {
        const yours = picked === -1 ? "No answer (time ran out)" : q.options[picked];
        lines.push(
          "",
          `${n + 1}. ${q.question}`,
          `   Your answer: ${yours}`,
          `   Correct answer: ${q.options[q.correctIndex]}`,
          `   ${q.explanation}`
        );
      });
    }
    return lines.join("\n");
  }

  async function copyResult() {
    const text = buildResultText();
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard can be blocked by the browser; nothing else to do.
    }
  }

  return (
    <section>
      <p className="lede">
        {quiz.topic} - {quiz.difficulty}
      </p>
      <h1>
        {score} out of {total}
      </h1>
      <p className="lede">{messageFor(score / total)}</p>

      <div className="actions">
        <button className="primary" type="button" onClick={onRetry}>
          Try this topic again
        </button>
        <button className="ghost" type="button" onClick={onNewTopic}>
          New topic
        </button>
        <button className="ghost" type="button" onClick={copyResult}>
          {copied ? "Copied!" : "Copy result"}
        </button>
      </div>

      {misses.length > 0 && (
        <div>
          <h2>Questions to review</h2>
          {misses.map(({ q, picked }) => (
            <div className="review-item" key={q.question}>
              <p className="q">{q.question}</p>
              <p className="yours">
                Your answer: {picked === -1 ? "No answer (time ran out)" : q.options[picked]}
              </p>
              <p className="right">Correct answer: {q.options[q.correctIndex]}</p>
              <p>{q.explanation}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
