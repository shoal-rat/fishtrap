<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <img src="assets/banner.jpg" alt="fishtrap: an ink-wash bamboo fish trap with a carp" width="100%">
</p>

<h1 align="center">fishtrap</h1>

<p align="center"><b>Get the fish. Forget the trap.</b><br>
Keeps GPT agents in Codex working toward what you actually want, and stops them hedging every sentence.</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2f5d8a" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/works%20with-Codex%20CLI%20%26%20app-1f2933" alt="Works with Codex CLI and app">
  <img src="https://img.shields.io/badge/dependencies-none-1a7f37" alt="No dependencies">
  <a href="https://github.com/shoal-rat/fishtrap-bench"><img src="https://img.shields.io/badge/benchmark-fishtrap--bench-b4540a" alt="fishtrap-bench"></a>
  <!-- ARXIV_BADGE -->
</p>

---

I asked a GPT-6.1 agent to upload a photo to a job application. It picked a photo I had made for the civil-service exam and uploaded it under its original name, `国考报名照片.JPG`. The upload worked. The employer got a file labelled for another purpose.

None of these failures comes from missing knowledge. The same agent had named an earlier file correctly in that very session. What goes wrong is where it points: it satisfies the instruction and the checks it can see, and loses sight of the person who will receive the result. Over a month of real sessions I found 27 such incidents, and they fell into five patterns. fishtrap addresses those patterns where they happen.

<p align="center"><img src="assets/before-after.svg" alt="Four moments where GPT drifts, with and without fishtrap" width="100%"></p>

## Install: tell your agent

Paste this into Codex (CLI or desktop app):

```text
Install fishtrap for me: https://github.com/shoal-rat/fishtrap — follow its INSTALL.md.
```

The agent asks for one thing, the name you put on files you send, then clones the repo, runs the installer, and reports back. You do the last step yourself, because Codex runs a hook only after a person trusts it: open **Settings → Hooks** in the app (or type `/hooks` in the CLI), trust the five fishtrap hooks, and start a new session.

<details>
<summary>Install by hand</summary>

```bash
git clone --depth 1 https://github.com/shoal-rat/fishtrap ~/.fishtrap
python3 ~/.fishtrap/install.py --name "Your Name" --alt-names "其他写法,Other Spelling" --profile ~/path/to/your-profile.md
```

Then trust the hooks as above. `--profile` is optional: point it at a résumé or notes file if you keep one. The installer backs up `~/.codex/AGENTS.md` and `~/.codex/hooks.json` first, and running it again updates in place.

</details>

<details>
<summary>ChatGPT on the web or in the app</summary>

Hooks need Codex, but the principles work anywhere. Paste [`fishtrap/chatgpt-custom-instructions.md`](fishtrap/chatgpt-custom-instructions.md) into **Settings → Personalization → Custom instructions** and start a new chat.

</details>

## How it works

fishtrap has two layers.

**1. Principles with their reasons.** A short block at the top of `AGENTS.md` tells the model to work out who will judge the result before acting, to treat counts and required fields as constraints inside your goal, and to apply each rule as far as its reason reaches. A rule without its reason gets applied too far or not far enough, so every rule carries its reason. It also covers writing: lead with the answer, qualify only what is actually uncertain, and write on your behalf as your advocate.

**2. Five hooks at the moments of drift.** Instructions read at session start fade a hundred tool calls later, and that is when the damage happens: six of the seven serious incidents I found occurred where content leaves the machine. So the hooks act there.

<p align="center"><img src="assets/how-it-works.svg" alt="The five fishtrap hooks on a session timeline" width="100%"></p>

| Hook | When it fires | What it asks the model |
|---|---|---|
| Recipient check | before an upload | What will the reader see in this file name and this file? |
| Readback | before a submit or send | Does this match what the user asked for, field by field? |
| Validation reframe | after a "required / incomplete" message | Should this entry be here at all? Fix it the way the reviewer would want. |
| Brief recall | on a new count, "continue", "I'm logged in", and after compaction | What were the original criteria, and what parked work can resume now? |
| Closure check | at the end of a substantial turn | Is every part of the request done, as observed rather than assumed? |

Each hook asks once and then lets the model continue. It never makes the decision itself, and a retry goes through. The hook script uses only the Python standard library, makes no network requests, keeps its state in `~/.codex/hooks/fishtrap/`, and exits silently if anything goes wrong, so a bug in fishtrap can never block your agent.

## Does it work?

<!-- RESULTS -->

The benchmark, its graders and every run are public in [fishtrap-bench](https://github.com/shoal-rat/fishtrap-bench). The paper has the field study, the design and the full evaluation.

## FAQ

**Will it make the agent reckless?** The benchmark checks for that too. Half its checks are guards that fail an agent for over-correcting: stripping required information, refusing to submit, renaming files the destination named, or asking questions it could have answered itself.

**Does it cost many tokens?** The principles block is about 1,300 tokens, read once per session. Hooks add a short message only when they fire. Measured costs are in the results above.

**Is it only for job applications?** The incidents came from job applications, and the benchmark is written around them, because that is where the cost of a stray file name is easiest to see. The principles and hooks are general: any upload, send, form, or long multi-step task.

**What does it change on my machine?** Three things in `~/.codex` (or `$CODEX_HOME`): a marked block at the top of `AGENTS.md`, five entries in `hooks.json`, and the folder `hooks/fishtrap/`. Your own instructions and hooks stay as they were.

**How do I check or remove it?**

```bash
python3 ~/.fishtrap/install.py --check       # what is installed, recent hook activity
python3 ~/.fishtrap/install.py --uninstall   # removes only fishtrap, keeps a backup
```

## Why "fishtrap"

> 筌者所以在鱼，得鱼而忘筌。
> The fish trap exists for the fish; once you have the fish, you can forget the trap. — *Zhuangzi*

Instructions, counts, and validation checks are traps for catching what you want. An agent that holds on to the trap and forgets the fish uploads `国考报名照片.JPG`. fishtrap keeps it looking at the fish.

## Citation

<!-- CITATION -->

## License

MIT. See [LICENSE](LICENSE).
