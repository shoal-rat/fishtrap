# Installing fishtrap — instructions for AI agents

You are an AI agent, and the user asked you to install fishtrap. Follow these steps in order. The whole job takes a few minutes and needs one answer from the user at most.

## If you can run shell commands (Codex CLI, Codex desktop app, any coding agent)

1. **Get one fact from the user, unless you already know it:** the name they want on files they send to others (for example `Lin Zhiyuan` or `林知远`), plus any other spellings of it. If they keep a résumé or profile file, note its path too. Ask nothing else.
2. **Get the code.**
   ```bash
   git clone --depth 1 https://github.com/shoal-rat/fishtrap ~/.fishtrap 2>/dev/null || git -C ~/.fishtrap pull --ff-only
   ```
3. **Run the installer.** It writes to `~/.codex` (or `$CODEX_HOME`). If your sandbox blocks writes outside the workspace, request permission for this one command.
   ```bash
   python3 ~/.fishtrap/install.py --name "<name>" --alt-names "<other spellings, comma-separated>" --profile "<profile path, if any>"
   ```
   Leave out `--alt-names` or `--profile` when you have nothing for them. The installer backs up the user's files, adds a marked block to the top of `AGENTS.md`, merges five hooks into `hooks.json`, and runs a self-test.
4. **Report in three lines:** what was installed, where the backup is, and the self-test result.
5. **Hand the last step to the user.** Codex runs a hook only after a person trusts it, so this step belongs to them:
   - Codex desktop app: **Settings → Hooks** (or **Review hooks** above the composer), then trust the five fishtrap hooks.
   - Codex CLI: type `/hooks` in a session and trust them.
   - Then start a new session.

   Never write hook trust entries into `config.toml` yourself.
6. **Look for conflicts.** Read the rest of the user's `AGENTS.md`. If any rule there works against fishtrap (for example "always add a disclaimer", "ask before every step", or "pad every answer with caveats"), quote those lines to the user and ask whether to keep them. Do not edit or delete them yourself.

To check the installation later, run `python3 ~/.fishtrap/install.py --check`. To remove it, run `python3 ~/.fishtrap/install.py --uninstall`, which strips only fishtrap's block and hooks and leaves a backup.

## If you cannot run commands (ChatGPT on the web or in the app)

Give the user the text in [`fishtrap/chatgpt-custom-instructions.md`](fishtrap/chatgpt-custom-instructions.md) inside a code block. Tell them to paste it into **Settings → Personalization → Custom instructions → "How would you like ChatGPT to respond?"** and to start a new chat. That version carries the principles only; the hooks need Codex.
