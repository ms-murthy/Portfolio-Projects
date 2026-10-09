import { useState } from "react";

const TOPIC_IDEAS = [
  "Ancient Rome",
  "The human brain",
  "80s rock bands",
  "Space exploration",
  "World cuisines",
  "Shakespeare",
];
const DIFFICULTIES = ["easy", "medium", "hard"];

export default function SetupForm({ onStart, error, history, onClearHistory }) {
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [timed, setTimed] = useState(false);

  function handleSubmit(event) {
    event.preventDefault();
    onStart({ topic: topic.trim(), difficulty, timed });
  }

  return (
    <section>
      <h1>Quiz yourself on anything.</h1>
      <p className="lede">
        Name a topic and get a quiz written on the spot, with an explanation for every answer.
      </p>

      <form onSubmit={handleSubmit}>
        <label htmlFor="topic">Topic</label>
        <input
          id="topic"
          type="text"
          maxLength={200}
          placeholder="e.g. Ancient Rome"
          autoComplete="off"
          required
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />

        <div className="chips">
          {TOPIC_IDEAS.map((idea) => (
            <button key={idea} type="button" className="chip" onClick={() => setTopic(idea)}>
              {idea}
            </button>
          ))}
        </div>

        <fieldset>
          <legend>Difficulty</legend>
          <div className="segmented">
            {DIFFICULTIES.map((level) => (
              <label key={level}>
                <input
                  type="radio"
                  name="difficulty"
                  value={level}
                  checked={difficulty === level}
                  onChange={() => setDifficulty(level)}
                />
                <span>{level[0].toUpperCase() + level.slice(1)}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="row">
          <label className="check">
            <input type="checkbox" checked={timed} onChange={(e) => setTimed(e.target.checked)} />
            30-second timer per question
          </label>
        </div>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="primary">
          Build my quiz
        </button>
      </form>

      {history.length > 0 && (
        <div id="history-box">
          <h2>Your recent quizzes</h2>
          <ul id="history">
            {history.map((item) => (
              <li key={item.date}>
                <span>
                  {item.topic} ({item.difficulty})
                </span>
                <span className="meta">
                  {item.score}/{item.total} - {new Date(item.date).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
          <button className="ghost" type="button" onClick={onClearHistory}>
            Clear history
          </button>
        </div>
      )}
    </section>
  );
}
