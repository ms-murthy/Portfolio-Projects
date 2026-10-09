// Past scores are kept in this browser only (localStorage).
const KEY = "quizforge-history";

export function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || [];
  } catch {
    return [];
  }
}

// Saves a new entry at the top and returns the updated list (max 20).
export function saveHistory(entry) {
  const list = [entry, ...loadHistory()].slice(0, 20);
  localStorage.setItem(KEY, JSON.stringify(list));
  return list;
}

export function clearHistory() {
  localStorage.removeItem(KEY);
  return [];
}
