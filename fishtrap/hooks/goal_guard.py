#!/usr/bin/env python3
"""fishtrap: Codex hooks that keep GPT anchored to the user's goal at the moments it drifts.

One script, dispatched on hook_event_name:
  UserPromptSubmit  remember the brief; re-inject it when a new turn sets a count, continues, or unblocks
  SessionStart      re-inject the brief after compaction/resume
  PreToolUse        recipient check before an upload, readback before a submit/send (deny once, then allow)
  PostToolUse       reframe validation flags ("必填/不完整") toward the reviewer's view
  Stop              one closure check per substantial turn

Any internal error exits 0 with no output, so a bug never blocks Codex.
"""
import hashlib
import json
import os
import re
import sys
import time

HOME = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
STATE_DIR = os.path.join(HOME, "hooks", "fishtrap", "state")
LOG_PATH = os.path.join(HOME, "hooks", "fishtrap", "goal_guard.log")


def _load_names():
    """Names that should identify the user in outgoing file names.
    Set GOAL_GUARD_NAMES="名字,Given,FAMILY" or put {"names": [...]} in goal_guard.json next to this script."""
    env = os.environ.get("GOAL_GUARD_NAMES")
    if env:
        return tuple(n.strip() for n in env.split(",") if n.strip())
    try:
        cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "goal_guard.json")
        with open(cfg, encoding="utf-8") as f:
            return tuple(json.load(f).get("names") or ())
    except Exception:
        return ()


CANDIDATE_NAMES = _load_names()
NAME_HINT = (CANDIDATE_NAMES[0] if CANDIDATE_NAMES else "<your name>") + "_<材料名>.<ext>"

# A gate fires again for the same thing only after this many tool calls.
UPLOAD_REGATE_CALLS = 40
SUBMIT_REGATE_CALLS = 20
VALIDATION_REGATE_CALLS = 15
STOP_MIN_CALLS = 12

UPLOAD_JS = re.compile(r"\bset(?:Input)?Files\s*\(")
JS_PATH = re.compile(r"""['"`](/[^'"`\n]+?\.[A-Za-z0-9]{2,5})['"`]""")
SUBMIT_WORDS = r"(?:确认提交|提交申请|提交简历|提交报名|立即投递|确认投递|立即申请|申请职位|一键投递|投递简历|交卷|提交|投递|发送|Submit|Send|Apply)"
SUBMIT_JS = re.compile(SUBMIT_WORDS + r"[\s\S]{0,160}?\.(?:click|tap|dispatchEvent)\s*\(|\.(?:click|tap)\s*\([\s\S]{0,40}?" + SUBMIT_WORDS)
OUT_DIR_WORDS = r"(?:upload|outbox|attach|附件|上传)"
UPLOAD_SH = re.compile(
    r"(?:^|[\s;&|(])(?:cp|mv|ln|install|rsync|ditto)\b[^;&|\n]*?" + OUT_DIR_WORDS
    + r"|(?:shutil\.copy\w*|copyfile|write_bytes|write_text)[\s\S]{0,300}?" + OUT_DIR_WORDS
    + r"|" + OUT_DIR_WORDS + r"[\s\S]{0,300}?(?:shutil\.copy\w*|copyfile|write_bytes|write_text)", re.I)
# Only running a submit/send program counts; reading submit.py does not.
SUBMIT_SH = re.compile(
    r"(?:(?:^|[;&|(\n])\s*(?:\S*/)?|\b(?:python3?|sh|bash|zsh|node|ruby|perl)\s+(?:-\S+\s+)*(?:\S*/)?)"
    r"[\w.-]*(?:submit|send|deliver)[\w.-]*(?:\.py|\.sh|\.js)?(?=[\s;&|)]|$)"
    r"|osascript[\s\S]*\bsend\b", re.I)
PATCH_ADD = re.compile(r"\*\*\* (?:Add|Update) File:\s*(\S[^\n]*" + OUT_DIR_WORDS + r"[^\n]*)", re.I)
VALIDATION = re.compile(r"必填|不能为空|未填写|不完整|未完善|请完善|请补充|缺少|标黄|标红|\brequired\b|\bmissing\b|incomplete", re.I)
TARGET = re.compile(r"\d+\s*(?:个|份|家|条|道|题|篇|张|所)|[一二三四五六七八九十两几]+\s*(?:个|份|家|条)")
CONTINUE = re.compile(r"继续|接着|再(?:投|填|做|找|来)|先(?:投|填|做)|剩下|其余")
UNBLOCK = re.compile(r"登录|登陆|扫码|扫了|已打开|打开了|弄好了|好了|可以了|连上|恢复了|解锁")

NAME_FLAGS = [
    (re.compile(r"(?:^|[_\-\s.])v\d+|版本|终版|定稿|最终|final|draft|草稿", re.I), "a version or draft label"),
    (re.compile(r"副本|copy|\(\d+\)|（\d+）", re.I), "a duplicate marker"),
    (re.compile(r"压缩|原图|compressed|resized|temp|tmp|test|测试", re.I), "a processing label"),
    (re.compile(r"[0-9a-f]{12,}|codex-clipboard|reportlab|screenshot|截屏|屏幕快照|IMG_\d+", re.I), "a machine-generated name"),
    (re.compile(r"国考|省考|签证|护照照片|报名照片|[^_\-\s]{2,8}(?:申请用|专用|用版)"), "a label from another purpose"),
]


def log(event, detail=""):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 1_000_000:
            os.replace(LOG_PATH, LOG_PATH + ".1")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{event}\t{detail}\n")
    except Exception:
        pass


def state_path(sid):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", sid or "nosession")[:120]
    return os.path.join(STATE_DIR, safe + ".json")


def load_state(sid):
    try:
        with open(state_path(sid), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"calls": 0, "brief": None, "prompts": [], "turn_prompt": {}, "turn_calls": {},
                "outbound_turns": [], "gates": {}}


def save_state(sid, st):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        # keep per-turn maps small
        for k in ("turn_prompt", "turn_calls"):
            if len(st.get(k, {})) > 50:
                st[k] = dict(list(st[k].items())[-50:])
        st["outbound_turns"] = st.get("outbound_turns", [])[-50:]
        st["prompts"] = st.get("prompts", [])[-5:]
        tmp = state_path(sid) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False)
        os.replace(tmp, state_path(sid))
    except Exception:
        pass


def prune_old_states():
    try:
        cutoff = time.time() - 7 * 86400
        for name in os.listdir(STATE_DIR):
            p = os.path.join(STATE_DIR, name)
            if os.path.getmtime(p) < cutoff:
                os.remove(p)
    except Exception:
        pass


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.exit(0)


def clip(text, n):
    text = (text or "").strip()
    return text if len(text) <= n else text[:n] + "…"


def gate_due(st, key, every):
    """True when this gate should fire now; records the firing."""
    last = st["gates"].get(key)
    if last is not None and st["calls"] - last < every:
        return False
    st["gates"][key] = st["calls"]
    return True


def name_problems(basename):
    found = [label for rx, label in NAME_FLAGS if rx.search(basename)]
    if CANDIDATE_NAMES and not any(n in basename for n in CANDIDATE_NAMES):
        found.append("nothing that identifies the candidate")
    return found


def shell_upload_names(code):
    """Basenames that land in an upload/outbox/attachment folder via cp/mv/etc."""
    import shlex
    names = []
    for seg in re.split(r"&&|\|\||;|\n|\|", code):
        try:
            parts = shlex.split(seg)
        except ValueError:
            parts = seg.split()
        if not parts or parts[0] not in ("cp", "mv", "ln", "install", "rsync", "ditto"):
            continue
        args = [a for a in parts[1:] if not a.startswith("-")]
        if len(args) < 2 or not re.search(OUT_DIR_WORDS, args[-1], re.I):
            continue
        dest = args[-1]
        if re.search(r"\.[A-Za-z0-9]{2,5}$", dest) and not dest.endswith("/"):
            names.append(os.path.basename(dest))
        else:
            names.extend(os.path.basename(a.rstrip("/")) for a in args[:-1])
    if not names:  # python/heredoc copies: fall back to any file paths mentioned
        names = [os.path.basename(p) for p in re.findall(
            r"""['"]?((?:/|\./|[^\s'";&|]+/)[^\s'";&|]*\.[A-Za-z0-9]{2,5})['"]?""", code)]
    return names[:6]


def brief_block(st, latest=None):
    parts = []
    if st.get("brief"):
        parts.append("The user's original request in this session:\n«" + clip(st["brief"], 1200) + "»")
    if latest and latest != st.get("brief"):
        parts.append("Latest request:\n«" + clip(latest, 600) + "»")
    return "\n".join(parts)


def on_user_prompt(data, st):
    prompt = data.get("prompt") or ""
    turn = data.get("turn_id") or ""
    m = re.search(r"##\s*My request:\s*([\s\S]+)$", prompt)  # desktop app wraps the text
    text = (m.group(1) if m else prompt).strip()
    if turn:
        st["turn_prompt"][turn] = clip(text, 1500)
    first = st.get("brief") is None
    if first:
        st["brief"] = clip(text, 1500)
    st["prompts"].append(clip(text, 600))
    if first:
        return None
    notes = []
    if TARGET.search(text):
        notes.append("A number in a request sits inside the user's criteria. Count only items that meet them; if too few qualify, stop at what qualifies and say which criterion would have to relax.")
    if UNBLOCK.search(text):
        notes.append("The user just did something to unblock earlier work. Resume everything that was waiting on it, including items you parked or skipped.")
    if CONTINUE.search(text) and not notes:
        notes.append("This continues the earlier task: keep its criteria and quality bar.")
    if not notes:
        return None
    return brief_block(st) + "\n" + " ".join(notes)


def on_session_start(data, st):
    prune_old_states()
    if data.get("source") not in ("compact", "resume") or not st.get("brief"):
        return None
    latest = st["prompts"][-1] if st.get("prompts") else None
    return (brief_block(st, latest) + "\nPrecautions written down earlier in this session or by an earlier session "
            "are working assumptions; the user's newest message decides.")


def deny(reason):
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                 "permissionDecisionReason": reason}})


def on_pre_tool(data, st):
    tool = data.get("tool_name") or ""
    tin = data.get("tool_input") or {}
    turn = data.get("turn_id") or ""
    st["calls"] += 1
    if turn:
        st["turn_calls"][turn] = st["turn_calls"].get(turn, 0) + 1
    code = ""
    if isinstance(tin, dict):
        code = tin.get("code") or tin.get("command") or ""
        if isinstance(code, list):
            code = " ".join(map(str, code))
    elif isinstance(tin, str):
        code = tin
    code = str(code)
    is_js = tool.endswith("__js") or tool == "js"
    is_sh = tool in ("Bash", "exec_command", "shell", "local_shell")

    uploads = []  # basenames the recipient will see
    if is_js and UPLOAD_JS.search(code):
        uploads = [os.path.basename(p) for p in JS_PATH.findall(code)] or ["(a file)"]
    elif is_sh and UPLOAD_SH.search(code):
        uploads = shell_upload_names(code) or ["(a file)"]
    elif tool == "apply_patch" and PATCH_ADD.search(code):
        uploads = [os.path.basename(p.strip()) for p in PATCH_ADD.findall(code)][:6]
    submit = (is_js and SUBMIT_JS.search(code)) or (is_sh and SUBMIT_SH.search(code))

    if uploads or submit:
        if turn and turn not in st["outbound_turns"]:
            st["outbound_turns"].append(turn)

    if uploads:
        flagged = {b: name_problems(b) for b in uploads if b != "(a file)"}
        flagged = {b: p for b, p in flagged.items() if p}
        if flagged:  # each problematic name gets its own check
            key = "upload:" + hashlib.sha1("|".join(sorted(flagged)).encode()).hexdigest()[:16]
        else:  # clean names: one reflection per stretch of work
            key = "upload:clean"
        if gate_due(st, key, UPLOAD_REGATE_CALLS):
            lines = []
            for base in uploads:
                probs = flagged.get(base)
                lines.append(f"- {base}" + (f"  (its name contains {', '.join(probs)})" if probs else ""))
            log("PreToolUse", f"{tool}\tupload-gate\t{len(uploads)}")
            deny("Recipient check before this upload. The reviewer at the destination will see each file's name and "
                 "contents:\n" + "\n".join(lines) + "\n"
                 "Confirm each file was made for this destination and purpose, and that its name is what that reviewer "
                 "should see: normally " + NAME_HINT + ", or the naming rule the destination specifies, with no labels "
                 "from your own workflow or from other applications. If a file needs a new name, new size, or content "
                 "aimed at this destination, put a fixed copy in your working folder and upload that copy. If everything "
                 "already fits, run the same call again. Carry on without asking the user.")
    if submit:
        if gate_due(st, "submit", SUBMIT_REGATE_CALLS):
            log("PreToolUse", f"{tool}\tsubmit-gate")
            deny("Readback before submitting or sending. Look at the current form, message, or attachments again and read "
                 "every value and file name the way the receiving reviewer will. For each, ask what that reader concludes. "
                 "Fix anything that serves you or the form rather than that reader: entries in the wrong section, empty or "
                 "duplicate rows, placeholder or label-echo values, notes about the form, your sources, forced values or "
                 "your inferences (those go in your report to the user), and anything written for a different organisation. "
                 "Then run the submit again. Carry on without asking the user.")
    log("PreToolUse", f"{tool}\tallow")
    return None


def on_post_tool(data, st):
    resp = data.get("tool_response")
    text = resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)
    if not text or not VALIDATION.search(text[:20000]):
        return None
    if not gate_due(st, "validation", VALIDATION_REGATE_CALLS):
        return None
    log("PostToolUse", f"{data.get('tool_name')}\tvalidation-note")
    emit({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
          "A validation message is a symptom. Before filling anything it names, check that each flagged entry belongs in "
          "that section and should exist at all: move misplaced entries to the right section and delete empty or duplicate "
          "rows first. Fill only real values from the user's materials."}})


def on_stop(data, st):
    if data.get("stop_hook_active"):
        return None
    turn = data.get("turn_id") or ""
    calls = st["turn_calls"].get(turn, 0)
    outbound = turn in st.get("outbound_turns", [])
    if calls < STOP_MIN_CALLS and not outbound:
        return None
    if not gate_due(st, "stop:" + turn, 10**9):
        return None
    asked = st["turn_prompt"].get(turn) or (st["prompts"][-1] if st.get("prompts") else "")
    log("Stop", f"closure-check\tcalls={calls}\toutbound={outbound}")
    reason = ("Closure check before you finish this turn.\n"
              + ("The user asked: «" + clip(asked, 1200) + "»\n" if asked else "")
              + ("Original request of this session: «" + clip(st.get("brief"), 800) + "»\n"
                 if st.get("brief") and st.get("brief") != asked else "")
              + "1. Compare what now exists with the end state the user asked for, part by part, using what you actually "
                "observed (page state, files, receipts, command output).\n"
                "2. Anything you parked, skipped, or found blocked earlier: if it can be done now, do it now.\n"
                "3. Whatever a third party receives should read right to that reader. Forced values, assumptions, and "
                "anything the user must do belong in your final message to the user.\n"
                "If everything is done, end with your report. Ask only for a login, a QR-code scan, a payment, or a "
                "choice the user reserved.")
    emit({"decision": "block", "reason": reason})


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    event = data.get("hook_event_name") or ""
    sid = data.get("session_id") or ""
    st = load_state(sid)
    for k, v in (("gates", {}), ("turn_prompt", {}), ("turn_calls", {}), ("outbound_turns", []), ("prompts", []), ("calls", 0)):
        st.setdefault(k, v)
    try:
        if event == "UserPromptSubmit":
            ctx = on_user_prompt(data, st)
            save_state(sid, st)
            if ctx:
                log(event, "reinject")
                emit({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ctx}})
        elif event == "SessionStart":
            ctx = on_session_start(data, st)
            save_state(sid, st)
            if ctx:
                log(event, "reinject")
                emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}})
        elif event == "PreToolUse":
            try:
                on_pre_tool(data, st)
            finally:
                save_state(sid, st)
        elif event == "PostToolUse":
            try:
                on_post_tool(data, st)
            finally:
                save_state(sid, st)
        elif event == "Stop":
            try:
                on_stop(data, st)
            finally:
                save_state(sid, st)
    except SystemExit:
        raise
    except Exception as e:  # never block Codex because of a hook bug
        log("error", f"{event}\t{type(e).__name__}: {e}")
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
