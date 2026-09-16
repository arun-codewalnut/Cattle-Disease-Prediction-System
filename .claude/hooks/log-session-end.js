#!/usr/bin/env node
/**
 * Stop hook — automatic "capture" step for the agentic-retrospective workflow
 * (agents/playbooks/retrospective.md). Appends one line per session end to a local,
 * gitignored log. Deliberately does nothing beyond capture: analysis and rule changes stay
 * a deliberate, human-approved step (see the retrospective skill), not something this hook
 * does on its own.
 */
const fs = require("fs");
const path = require("path");

let input = "";
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", () => {
  let data = {};
  try {
    data = JSON.parse(input);
  } catch {
    // still log even if stdin wasn't parseable JSON
  }

  const logDir = path.join(__dirname, "..", "retro-logs");
  fs.mkdirSync(logDir, { recursive: true });

  const entry = {
    timestamp: new Date().toISOString(),
    session_id: data.session_id || null,
    transcript_path: data.transcript_path || null,
  };

  fs.appendFileSync(path.join(logDir, "sessions.jsonl"), JSON.stringify(entry) + "\n");
  process.exit(0);
});
