# Installing fishtrap — instructions for AI agents

You are an AI agent, and the user asked you to install fishtrap. Follow these steps in order. The job takes a few minutes and needs one answer from the user at most.

## If you can run shell commands (Codex CLI, Codex desktop app, any coding agent)

1. **Get one fact from the user, unless you already know it:** the name they want on files they send to others (for example `Lin Zhiyuan` or `林知远`), plus any other spellings of it. If they keep a résumé or profile file, note its path too. Ask nothing else.
2. **Get the code.** This needs network access; if your sandbox blocks it, request permission for this one command.
   ```bash
   git clone --depth 1 https://github.com/shoal-rat/fishtrap ~/.fishtrap 2>/dev/null || git -C ~/.fishtrap pull --ff-only
   ```
3. **Run the installer.** It writes to `~/.codex` (or `$CODEX_HOME`). If your sandbox blocks writes outside the workspace, request permission for this one command.
   ```bash
   python3 ~/.fishtrap/install.py --name "<name>" --alt-names "<other spellings, comma-separated>" --profile "<profile path, if any>"
   ```
   Pass each spelling as its own item in `--alt-names` (`"林知远,Zhiyuan LIN"`). Leave out `--alt-names` or `--profile` when you have nothing for them. The installer backs up the user's `AGENTS.md` and adds a marked block to its top.
4. **Report in two lines:** what was installed and where the backup is. Tell the user to start a new Codex session, because running sessions keep their old instructions.
5. **Look for conflicts.** Read the rest of the user's `AGENTS.md`. If any rule there works against fishtrap (for example "always add a disclaimer", "ask before every step", or "pad every answer with caveats"), quote those lines to the user and ask whether to keep them. Do not edit or delete them yourself.

### Only if the user asks for the hooks

fishtrap also ships five experimental Codex hooks. In our evaluation they added about a fifth to token use and time without improving results over the principles alone, so they are off by default. If the user asks for them, run the installer again with `--hooks`. Codex runs a hook only after a person trusts it, so that step belongs to the user: in the desktop app, **Settings → Hooks**; in the CLI, `/hooks`. Never write hook trust entries into `config.toml` yourself.

To check the installation later, run `python3 ~/.fishtrap/install.py --check`. To remove it, run `python3 ~/.fishtrap/install.py --uninstall`, which strips only fishtrap's additions and leaves a backup.

## If you cannot run commands (ChatGPT on the web or in the app)

Give the user the text in [`fishtrap/chatgpt-custom-instructions.md`](fishtrap/chatgpt-custom-instructions.md) inside a code block. Tell them to paste it into **Settings → Personalization → Custom instructions → "How would you like ChatGPT to respond?"** and to start a new chat.
