#!/usr/bin/env node
/**
 * PreToolUse guardrail for Bash. Static permission rules can't catch a dangerous command
 * hidden behind a benign-looking prefix (e.g. `cd x && rm -rf /`), so this inspects the
 * actual command string. Exit 2 blocks the tool call and feeds stderr back as the reason;
 * exit 0 allows it. See docs/DISCLAIMER.md-adjacent guardrail intent in AGENTS.md.
 */
let input = "";
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", () => {
  let data;
  try {
    data = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  if (data.tool_name !== "Bash") process.exit(0);

  const command = (data.tool_input && data.tool_input.command) || "";

  const DANGEROUS = [
    { pattern: /rm\s+-rf\s+\/(?!\S)/, reason: "rm -rf on a root path" },
    { pattern: /git\s+push\b.*--force(?!-with-lease)/, reason: "force push without --force-with-lease" },
    { pattern: /git\s+reset\s+--hard/, reason: "git reset --hard (discards uncommitted work)" },
    { pattern: /--dangerously-skip-permissions/, reason: "YOLO mode flag" },
    { pattern: /\.env\b.*(cat\s|type\s|Get-Content)/i, reason: "reading a .env file directly" },
    { pattern: /\bcat\s+.*\.env\b/i, reason: "reading a .env file directly" },
  ];

  for (const { pattern, reason } of DANGEROUS) {
    if (pattern.test(command)) {
      process.stderr.write(
        `Blocked by project guardrail (.claude/hooks/block-dangerous-bash.js): ${reason}.\n` +
          `If this is genuinely intended, ask the user to run it manually instead.\n`
      );
      process.exit(2);
    }
  }

  process.exit(0);
});
