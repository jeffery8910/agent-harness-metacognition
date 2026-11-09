#!/usr/bin/env python3
"""PreToolUse hook（R2 前置檢查）。

Agent 要執行 `wrangler deploy` 時，先確認目前登入的 Cloudflare 帳號
是 EXPECTED_CF_EMAIL。帳號不符或無法確認，就以 exit code 2 擋下。

- 沒設定 EXPECTED_CF_EMAIL：不檢查，直接放行（這個檢查是選用的）。
- PREFLIGHT_WHOAMI_CMD：可替換查詢帳號的指令（預設 `npx --yes wrangler whoami`）。
"""
import json
import os
import re
import subprocess
import sys

DEPLOY_PATTERN = re.compile(r"\bwrangler\b[^\n;&|]*\bdeploy\b")


def block(msg: str) -> int:
    print(f"[preflight-deploy] {msg}。已擋下部署，請先確認帳號，不要換個指令繞過。", file=sys.stderr)
    return 2


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    command = (data.get("tool_input") or {}).get("command", "")
    if data.get("tool_name") != "Bash" or not DEPLOY_PATTERN.search(command):
        return 0

    expected = os.environ.get("EXPECTED_CF_EMAIL", "").strip()
    if not expected:
        return 0

    whoami = os.environ.get("PREFLIGHT_WHOAMI_CMD", "npx --yes wrangler whoami")
    try:
        result = subprocess.run(whoami, shell=True, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return block("查詢 Cloudflare 帳號逾時")

    output = result.stdout + result.stderr
    if result.returncode != 0:
        return block(f"無法查詢 Cloudflare 帳號（{whoami} 結束碼 {result.returncode}）")
    if expected.lower() not in output.lower():
        return block(f"目前登入的 Cloudflare 帳號不是 {expected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
