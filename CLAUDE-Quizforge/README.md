# Quizforge

Type a topic, pick a difficulty, and get an AI-written 10-question multiple-choice quiz with an explanation for every answer and a final score.

Built with React + Vite (frontend) and Node/Express (backend) calling the Anthropic API.

## Run it
1. Install Node.js (version 20.19 or newer) from https://nodejs.org
2. In this folder, run: `npm install` (installs both `client/` and `server/`)
3. Copy `.env.example` to `.env` and paste your Anthropic API key
4. Run: `npm run dev`
5. Open http://localhost:5173

## Run the production version
```
npm run build   # builds the React app into client/dist
npm start       # Express serves it at http://localhost:4000
```

## How it works
- `client/` is the React app (what you see in the browser). `App.jsx` decides which screen shows: setup, loading, quiz, or results
- `server/index.js` receives the topic, asks Claude for a quiz as JSON, checks the JSON, and sends it back
- In development, Vite (port 5173) forwards `/api` requests to Express (port 4000)
- Your API key stays in `.env` on the server and never reaches the browser
- Past scores and your theme are saved in your browser only (localStorage)

## Folder map
```
.env / .env.example     API key (real one is git-ignored)
server/index.js         Express API: POST /api/quiz
client/src/App.jsx      app state and screen switching
client/src/api.js       the fetch call to the server
client/src/components/  SetupForm, Question, Results
```

## Ideas to add with Claude Code
- Quiz from pasted notes or an uploaded PDF
- A score chart from the saved history
- "Harder questions on the same topic" button
- Sound effects and a streak counter
- Accounts and a leaderboard (needs a database)
