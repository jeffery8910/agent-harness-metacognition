#!/usr/bin/env python3
"""PostToolUse hook（R3 動作後驗證）。

每次 Write／Edit／MultiEdit 之後讀回檔案，確認內容真的寫進去了。
對不上時以 exit code 2 結束，Claude Code 會把 stderr 的訊息交給 Agent，
讓它重新讀檔處理，而不是直接回報完成。
"""
import json
import pathlib
import sys


def norm(text: str) -> str:
    return text.replace("\r\n", "\n")


def fail(msg: str) -> int:
    print(f"[verify-after-write] {msg}。請重新讀取檔案確認並修正，不要直接回報完成。", file=sys.stderr)
    return 2


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # 讀不懂輸入就不介入，避免擋住正常工作

    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    path = ti.get("file_path")
    if tool not in ("Write", "Edit", "MultiEdit") or not path:
        return 0

    p = pathlib.Path(path)
    if not p.is_file():
        return fail(f"{tool} 回報成功，但檔案不存在：{path}")

    actual = norm(p.read_text(encoding="utf-8", errors="replace"))

    if tool == "Write":
        if actual != norm(ti.get("content", "")):
            return fail(f"Write 回報成功，但 {path} 的內容和要寫入的不一致")
    else:
        edits = ti.get("edits") if tool == "MultiEdit" else [ti]
        for i, edit in enumerate(edits or [], 1):
            new = norm(edit.get("new_string", ""))
            if new and new not in actual:
                return fail(f"{tool} 回報成功，但 {path} 找不到第 {i} 段修改後的文字")
    return 0


if __name__ == "__main__":
    sys.exit(main())
