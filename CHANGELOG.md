# Changelog

## 1.1.0

Based on the fishtrap-bench evaluation of 1.0.0 (240 runs; see the paper).

- The installer now installs the principles only. The hooks added cost without adding benefit in the evaluation, so they are opt-in with `--hooks`.
- Closure check (Stop hook): finishes parked work only when the user asked for it, and leaves alone steps the user kept, such as a final hand-in. In the evaluation, the 1.0.0 wording led the agent to hand in a test the user had reserved.
- Validation note (PostToolUse hook): fills remaining fields with values taken from or inferred from the user's materials, names the inference, and never enters a placeholder. The 1.0.0 wording ("fill only real values") conflicted with the principles' rule on deriving facts.
- Upload check: matches the user's name regardless of spaces, underscores, hyphens and, for names of five or more letters, case (`Zhiyuan LIN` matches `zhiyuan_lin_cv.pdf`).
- Hooks recognise English requests that add a count, continue, or unblock work.
- The hook changes above have not been re-evaluated.

## 1.0.0

The version evaluated in the paper: principles in `AGENTS.md` plus five Codex hooks, installed together by default.
