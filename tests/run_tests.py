#!/usr/bin/env python3
"""自動測試：hooks、證據檢查器、伺服器判定範例、規則檔一致性。

執行：python3 tests/run_tests.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
results = []


def run_hook(script, payload, env=None):
    return subprocess.run(
        [PY, str(ROOT / "hooks" / script)],
        input=json.dumps(payload), capture_output=True, text=True,
        env={**os.environ, **(env or {})},
    )


def case(name, ok, detail=""):
    results.append(ok)
    print(f"{'✓' if ok else '✗'} {name}" + (f"：{detail}" if detail and not ok else ""))


# ---- verify_write.py ----
with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "a.txt"
    f.write_text("hello\nworld\n", encoding="utf-8")

    r = run_hook("verify_write.py", {"tool_name": "Write", "tool_input": {"file_path": str(f), "content": "hello\nworld\n"}})
    case("verify_write：內容一致時放行", r.returncode == 0, r.stderr)

    r = run_hook("verify_write.py", {"tool_name": "Write", "tool_input": {"file_path": str(f), "content": "something else"}})
    case("verify_write：內容不一致時擋下（exit 2）", r.returncode == 2 and "不一致" in r.stderr, r.stderr)

    r = run_hook("verify_write.py", {"tool_name": "Write", "tool_input": {"file_path": str(Path(d) / "missing.txt"), "content": "x"}})
    case("verify_write：檔案不存在時擋下", r.returncode == 2 and "不存在" in r.stderr, r.stderr)

    r = run_hook("verify_write.py", {"tool_name": "Edit", "tool_input": {"file_path": str(f), "old_string": "x", "new_string": "lo\nwor"}})
    case("verify_write：Edit 多行新文字存在時放行", r.returncode == 0, r.stderr)

    r = run_hook("verify_write.py", {"tool_name": "MultiEdit", "tool_input": {"file_path": str(f), "edits": [{"new_string": "hello"}, {"new_string": "nope"}]}})
    case("verify_write：MultiEdit 有一段沒寫入時擋下", r.returncode == 2 and "第 2 段" in r.stderr, r.stderr)

    crlf = Path(d) / "crlf.txt"
    crlf.write_bytes(b"a\r\nb\r\n")
    r = run_hook("verify_write.py", {"tool_name": "Write", "tool_input": {"file_path": str(crlf), "content": "a\nb\n"}})
    case("verify_write：忽略 Windows 換行差異", r.returncode == 0, r.stderr)

r = run_hook("verify_write.py", {"tool_name": "Read", "tool_input": {"file_path": "/nope"}})
case("verify_write：其他工具不介入", r.returncode == 0)

# ---- preflight_deploy.py ----
deploy = {"tool_name": "Bash", "tool_input": {"command": "cd app && npx wrangler deploy"}}
ok_cmd = f'"{PY}" -c "print(\'associated with the email you@example.com\')"'
bad_cmd = f'"{PY}" -c "print(\'associated with the email other@example.com\')"'
fail_cmd = f'"{PY}" -c "import sys; sys.exit(1)"'

r = run_hook("preflight_deploy.py", deploy, {"EXPECTED_CF_EMAIL": "you@example.com", "PREFLIGHT_WHOAMI_CMD": ok_cmd})
case("preflight：帳號正確時放行", r.returncode == 0, r.stderr)

r = run_hook("preflight_deploy.py", deploy, {"EXPECTED_CF_EMAIL": "you@example.com", "PREFLIGHT_WHOAMI_CMD": bad_cmd})
case("preflight：帳號不符時擋下", r.returncode == 2 and "不是 you@example.com" in r.stderr, r.stderr)

r = run_hook("preflight_deploy.py", deploy, {"EXPECTED_CF_EMAIL": "you@example.com", "PREFLIGHT_WHOAMI_CMD": fail_cmd})
case("preflight：查不到帳號時擋下", r.returncode == 2 and "無法查詢" in r.stderr, r.stderr)

r = run_hook("preflight_deploy.py", {"tool_name": "Bash", "tool_input": {"command": "npm test"}}, {"EXPECTED_CF_EMAIL": "you@example.com", "PREFLIGHT_WHOAMI_CMD": bad_cmd})
case("preflight：非部署指令不介入", r.returncode == 0)

env_unset = {k: v for k, v in os.environ.items() if k != "EXPECTED_CF_EMAIL"}
r = subprocess.run([PY, str(ROOT / "hooks" / "preflight_deploy.py")], input=json.dumps(deploy), capture_output=True, text=True, env=env_unset)
case("preflight：未設定帳號時不檢查", r.returncode == 0, r.stderr)

# ---- check_evidence.py ----
checker = ROOT / "examples" / "evidence-report" / "check_evidence.py"
r = subprocess.run([PY, str(checker), str(checker.parent / "good.json")], capture_output=True, text=True)
case("check_evidence：good.json 通過", r.returncode == 0, r.stdout)

r = subprocess.run([PY, str(checker), str(checker.parent / "bad.json")], capture_output=True, text=True)
expected = ["沒有附來源", "已經發生", "unverified_scope"]
case("check_evidence：bad.json 抓出三類問題", r.returncode == 1 and all(e in r.stdout for e in expected), r.stdout)

# ---- server-authority ----
r = subprocess.run(["node", str(ROOT / "examples" / "server-authority" / "judge.mjs")], capture_output=True, text=True)
case("judge.mjs：伺服器判定阿明、客戶端判定小美", r.returncode == 0 and "伺服器時間判定：阿明" in r.stdout and "客戶端時間判定：小美" in r.stdout, r.stdout + r.stderr)

# ---- 規則檔一致性 ----
def rule_ids(path):
    return re.findall(r"\*\*(R\d+) ", (ROOT / path).read_text(encoding="utf-8"))

a, s = rule_ids("AGENTS.md"), rule_ids("skills/metacognitive-workflow/SKILL.md")
case("AGENTS.md 與 SKILL.md 的規則編號一致（R1–R11）", a == s == [f"R{i}" for i in range(1, 12)], f"{a} vs {s}")

for p in [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", "hooks/hooks.json", "examples/evidence-report/report.schema.json"]:
    try:
        json.loads((ROOT / p).read_text(encoding="utf-8"))
        case(f"{p} 是合法 JSON", True)
    except json.JSONDecodeError as e:
        case(f"{p} 是合法 JSON", False, str(e))

print(f"\n{sum(results)}/{len(results)} 通過")
sys.exit(0 if all(results) else 1)
