import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development, Vite serves the React app on port 5173 and forwards
// any request starting with /api to the Express server on port 4000.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:4000" },
  },
});
