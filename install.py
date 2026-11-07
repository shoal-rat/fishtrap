#!/usr/bin/env python3
"""Install, update, or remove fishtrap for OpenAI Codex (CLI and desktop app).

    python3 install.py --name "Lin Zhiyuan" [--alt-names "林知远,LIN"] [--profile ~/Documents/me.md] [--hooks]
    python3 install.py --uninstall
    python3 install.py --check

What it touches (and backs up first, under $CODEX_HOME/fishtrap-backups/<time>/):
  $CODEX_HOME/AGENTS.md      a block between <!-- fishtrap:begin --> and <!-- fishtrap:end -->
With --hooks (experimental; in our evaluation they added cost without adding benefit):
  $CODEX_HOME/hooks.json     fishtrap's five hook entries, merged with any hooks you already have
  $CODEX_HOME/hooks/fishtrap/ the hook script and its config

Standard library only. Safe to run again: it replaces its own block and entries and leaves everything else alone.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

VERSION = "1.1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
SNIPPET = os.path.join(HERE, "fishtrap", "AGENTS.fishtrap.md")
HOOK_SRC = os.path.join(HERE, "fishtrap", "hooks", "goal_guard.py")
BEGIN = "<!-- fishtrap:begin v%s -->" % VERSION
BEGIN_PREFIX = "<!-- fishtrap:begin"
END = "<!-- fishtrap:end -->"
HOOK_TAG = "fishtrap/goal_guard.py"


def codex_home(arg):
    return os.path.abspath(os.path.expanduser(arg or os.environ.get("CODEX_HOME") or "~/.codex"))


def backup(home, paths):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dst = os.path.join(home, "fishtrap-backups", stamp)
    n = 1
    while os.path.exists(dst):
        dst = os.path.join(home, "fishtrap-backups", "%s-%d" % (stamp, n))
        n += 1
    saved = []
    for p in paths:
        if os.path.exists(p):
            os.makedirs(dst, exist_ok=True)
            shutil.copy2(p, os.path.join(dst, os.path.basename(p)))
            saved.append(os.path.basename(p))
    return dst if saved else None


def strip_block(text):
    """Remove an existing fishtrap block (any version)."""
    start = text.find(BEGIN_PREFIX)
    if start < 0:
        return text, False
    end = text.find(END, start)
    if end < 0:
        raise SystemExit("AGENTS.md has a fishtrap begin marker without an end marker; fix it by hand first.")
    end += len(END)
    rest = (text[:start] + text[end:]).lstrip("\n")
    return rest, True


def render_snippet(name, profile):
    with open(SNIPPET, encoding="utf-8") as f:
        body = f.read()
    body = body.replace("{{NAME}}", name or "<your name>")
    if profile:
        line = "Take the user's facts and preferences from `%s`. " % profile
    else:
        line = "Take the user's facts from their own materials (résumé, profile notes, earlier messages). "
    body = body.replace("{{PROFILE_LINE}}", line)
    return "%s\n%s\n%s\n" % (BEGIN, body.strip(), END)


def hook_entries(script):
    cmd = "/usr/bin/env python3 '%s'" % script if os.name != "nt" else 'python "%s"' % script
    h = {"type": "command", "command": cmd, "timeout": 20}
    return {
        "UserPromptSubmit": [{"hooks": [dict(h)]}],
        "SessionStart": [{"matcher": "startup|resume|compact", "hooks": [dict(h)]}],
        "PreToolUse": [{"matcher": "^(mcp__cua_repl__js|Bash|apply_patch)$", "hooks": [dict(h)]}],
        "PostToolUse": [{"matcher": "^(mcp__cua_repl__js|Bash)$", "hooks": [dict(h)]}],
        "Stop": [{"hooks": [dict(h)]}],
    }


def remove_our_hooks(spec):
    hooks = spec.get("hooks") or {}
    for event in list(hooks):
        groups = []
        for g in hooks[event] or []:
            kept = [h for h in (g.get("hooks") or []) if HOOK_TAG not in str(h.get("command", ""))]
            if kept:
                g = dict(g, hooks=kept)
                groups.append(g)
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]
    spec["hooks"] = hooks
    return spec


def load_hooks(path):
    if not os.path.exists(path):
        return {"hooks": {}}
    with open(path, encoding="utf-8") as f:
        try:
            spec = json.load(f)
        except json.JSONDecodeError as e:
            raise SystemExit("%s is not valid JSON (%s); fix it first." % (path, e))
    spec.setdefault("hooks", {})
    return spec


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def self_test(script, names):
    """Feed the hook a fake upload and check it asks for a recipient check."""
    env = dict(os.environ, CODEX_HOME=os.path.join(os.path.dirname(script), ".selftest"),
               GOAL_GUARD_NAMES=",".join(names) or "Test")
    ev = {"hook_event_name": "PreToolUse", "session_id": "fishtrap-selftest", "turn_id": "t",
          "tool_name": "Bash", "tool_input": {"command": "cp drafts/resume_v3_final.pdf uploads/resume/"}}
    try:
        out = subprocess.run([sys.executable, script], input=json.dumps(ev), capture_output=True,
                             text=True, env=env, timeout=20).stdout
        ok = '"deny"' in out and "Recipient check" in out
    except Exception:
        ok = False
    shutil.rmtree(env["CODEX_HOME"], ignore_errors=True)
    return ok


def install(a):
    home = codex_home(a.codex_home)
    if not os.path.isdir(home):
        os.makedirs(home)
        print("Created %s (Codex had not created it yet)." % home)
    agents = os.path.join(home, "AGENTS.md")
    hooks_json = os.path.join(home, "hooks.json")
    names = [n for n in [a.name] + (a.alt_names.split(",") if a.alt_names else []) if n and n.strip()]
    names = [n.strip() for n in names]

    saved = backup(home, [agents, hooks_json])

    old = open(agents, encoding="utf-8").read() if os.path.exists(agents) else ""
    rest, had = strip_block(old)
    block = render_snippet(names[0] if names else None, a.profile)
    new = block + ("\n" + rest if rest.strip() else "")
    with open(agents, "w", encoding="utf-8") as f:
        f.write(new)

    hook_ok = None
    if a.hooks:
        hdir = os.path.join(home, "hooks", "fishtrap")
        os.makedirs(hdir, exist_ok=True)
        script = os.path.join(hdir, "goal_guard.py")
        shutil.copy2(HOOK_SRC, script)
        os.chmod(script, 0o755)
        write_json(os.path.join(hdir, "goal_guard.json"), {"names": names, "version": VERSION})
        spec = remove_our_hooks(load_hooks(hooks_json))
        for event, groups in hook_entries(script).items():
            spec["hooks"].setdefault(event, []).extend(groups)
        write_json(hooks_json, spec)
        hook_ok = self_test(script, names)

    if not a.hooks:
        old_hooks = sum(1 for gs in load_hooks(hooks_json)["hooks"].values() for g in gs
                        for h in g.get("hooks", []) if HOOK_TAG in str(h.get("command")))
        if old_hooks:
            print("Note: fishtrap hooks from an earlier install are still in hooks.json. Run with --hooks to update them,")
            print("      or --uninstall and then install again without --hooks to remove them.")
    print("fishtrap %s %s in %s" % (VERSION, "updated" if had else "installed", home))
    print("  AGENTS.md: fishtrap block %s at the top; your other instructions are unchanged."
          % ("replaced" if had else "added"))
    if a.hooks:
        print("  hooks.json: 5 fishtrap hooks merged (UserPromptSubmit, SessionStart, PreToolUse, PostToolUse, Stop).")
        print("  hook self-test: %s" % ("passed" if hook_ok else "FAILED - check that python3 runs"))
    if saved:
        print("  backup of your previous files: %s" % saved)
    print()
    print("NEXT STEP FOR THE HUMAN" + (" (an agent must not do this for them):" if a.hooks else ":"))
    if a.hooks:
        print("  Codex runs a hook only after a person trusts it. Approve the five fishtrap hooks:")
        print("   - Codex desktop app: Settings > Hooks (or 'Review hooks' above the composer) > trust them.")
        print("   - Codex CLI: type /hooks in a session and trust them.")
    print("  %s a new Codex session; running sessions keep their old instructions." % ("Then start" if a.hooks else "Start"))
    return 0


def uninstall(a):
    home = codex_home(a.codex_home)
    agents = os.path.join(home, "AGENTS.md")
    hooks_json = os.path.join(home, "hooks.json")
    saved = backup(home, [agents, hooks_json])
    if os.path.exists(agents):
        rest, had = strip_block(open(agents, encoding="utf-8").read())
        with open(agents, "w", encoding="utf-8") as f:
            f.write(rest)
        print("AGENTS.md: %s" % ("fishtrap block removed" if had else "no fishtrap block found"))
    if os.path.exists(hooks_json):
        write_json(hooks_json, remove_our_hooks(load_hooks(hooks_json)))
        print("hooks.json: fishtrap hooks removed")
    shutil.rmtree(os.path.join(home, "hooks", "fishtrap"), ignore_errors=True)
    try:
        os.rmdir(os.path.join(home, "hooks"))  # only succeeds if fishtrap left it empty
    except OSError:
        pass
    if saved:
        print("backup: %s" % saved)
    return 0


def check(a):
    home = codex_home(a.codex_home)
    agents = os.path.join(home, "AGENTS.md")
    text = open(agents, encoding="utf-8").read() if os.path.exists(agents) else ""
    i = text.find(BEGIN_PREFIX)
    print("AGENTS.md block: %s" % (text[i:text.find("-->", i) + 3] if i >= 0 else "missing"))
    spec = load_hooks(os.path.join(home, "hooks.json"))
    n = sum(1 for gs in spec["hooks"].values() for g in gs for h in g.get("hooks", []) if HOOK_TAG in str(h.get("command")))
    print("fishtrap hooks in hooks.json: %d of 5" % n)
    log = os.path.join(home, "hooks", "fishtrap", "goal_guard.log")
    if os.path.exists(log):
        lines = open(log, encoding="utf-8").read().splitlines()[-5:]
        print("last hook activity:\n  " + "\n  ".join(lines))
    else:
        print("no hook activity logged yet (hooks run after they are trusted and a new session starts)")
    return 0


def main():
    p = argparse.ArgumentParser(description="Install fishtrap into Codex.")
    p.add_argument("--name", help="the name the user wants on files they send, e.g. 'Lin Zhiyuan' or '林知远'")
    p.add_argument("--alt-names", help="other spellings that also identify the user, comma-separated")
    p.add_argument("--profile", help="path to the user's résumé/profile notes, if they keep one")
    p.add_argument("--codex-home", help="defaults to $CODEX_HOME or ~/.codex")
    p.add_argument("--hooks", action="store_true",
                   help="also install the five experimental hooks (they need a human to trust them in Codex)")
    p.add_argument("--no-hooks", action="store_true", help=argparse.SUPPRESS)  # the default since 1.1.0
    p.add_argument("--uninstall", action="store_true")
    p.add_argument("--check", action="store_true", help="show what is installed and recent hook activity")
    a = p.parse_args()
    if a.uninstall:
        return uninstall(a)
    if a.check:
        return check(a)
    return install(a)


if __name__ == "__main__":
    sys.exit(main())
