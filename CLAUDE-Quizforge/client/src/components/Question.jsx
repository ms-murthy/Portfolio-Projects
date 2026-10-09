import { useEffect, useRef, useState } from "react";

const LETTERS = ["A", "B", "C", "D"];
const SECONDS_PER_QUESTION = 30;

// Shows one question. `answers[index]` is the option the user picked
// (-1 means time ran out, undefined means not answered yet).
export default function Question({ quiz, index, answers, score, onAnswer, onNext }) {
  const question = quiz.questions[index];
  const picked = answers[index];
  const answered = picked !== undefined;
  const isLast = index === quiz.questions.length - 1;
  const correct = picked === question.correctIndex;

  // Countdown bar (only when the timer option was ticked)
  const [percentLeft, setPercentLeft] = useState(100);
  useEffect(() => {
    if (!quiz.timed || answered) return;
    const started = Date.now();
    const total = SECONDS_PER_QUESTION * 1000;
    const id = setInterval(() => {
      const left = total - (Date.now() - started);
      setPercentLeft(Math.max(0, (left / total) * 100));
      if (left <= 0) onAnswer(index, -1); // ran out of time
    }, 100);
    return () => clearInterval(id);
  }, [quiz.timed, answered, index, onAnswer]);

  // Move keyboard focus to "Next" after answering
  const nextRef = useRef(null);
  useEffect(() => {
    if (answered) nextRef.current?.focus();
  }, [answered]);

  function optionClass(i) {
    if (!answered) return "option";
    if (i === question.correctIndex) return "option correct";
    if (i === picked) return "option wrong";
    return "option";
  }

  return (
    <section>
      <div className="quiz-meta">
        <span>
          Question {index + 1} of {quiz.questions.length}
        </span>
        <span>Score: {score}</span>
      </div>

      {quiz.timed && (
        <div className="timer-track">
          <div id="timer-bar" style={{ width: percentLeft + "%" }} />
        </div>
      )}

      <h2>{question.question}</h2>

      <div className="options">
        {question.options.map((text, i) => (
          <button
            key={i}
            type="button"
            className={optionClass(i)}
            disabled={answered}
            onClick={() => onAnswer(index, i)}
          >
            <span className="letter">{LETTERS[i]}</span>
            <span>{text}</span>
          </button>
        ))}
      </div>

      {answered && (
        <div className={"feedback " + (correct ? "good" : "bad")}>
          <p id="feedback-title">
            {correct ? "Correct!" : picked === -1 ? "Time's up." : "Not quite."}
          </p>
          <p>{question.explanation}</p>
        </div>
      )}

      {answered && (
        <button ref={nextRef} className="primary" type="button" onClick={onNext}>
          {isLast ? "See my results" : "Next question"}
        </button>
      )}
    </section>
  );
}
