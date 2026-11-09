#!/usr/bin/env python3
"""檢查證據分級回報是否符合 R8。不需要安裝任何套件。

用法：python3 check_evidence.py report.json
全部通過結束碼 0；有問題結束碼 1，並列出每個問題。
"""
import json
import sys


def check(report: dict) -> list:
    problems = []
    if not str(report.get("result", "")).strip():
        problems.append("缺少 result：一句話說完成了什麼")
    if "unverified_scope" not in report:
        problems.append("缺少 unverified_scope：沒有未驗證的部分也要寫空陣列 []")

    for i, c in enumerate(report.get("claims", []), 1):
        label = f"第 {i} 個主張「{str(c.get('text', ''))[:20]}」"
        level = c.get("level")
        if level == "verified" and not c.get("sources"):
            problems.append(f"{label} 標為 verified 但沒有附來源")
        elif level == "inferred" and not str(c.get("basis", "")).strip():
            problems.append(f"{label} 標為 inferred 但沒有寫推論依據")
        elif level == "unverified" and not str(c.get("reason", "")).strip():
            problems.append(f"{label} 標為 unverified 但沒有寫原因")
        elif level not in ("verified", "inferred", "unverified"):
            problems.append(f"{label} 的 level 必須是 verified、inferred 或 unverified")
        if c.get("status") == "happened" and level != "verified":
            problems.append(f"{label} 說「已經發生」，卻不是 verified，請改成 possible 或補上來源")

    for i, s in enumerate(report.get("unverified_scope", []), 1):
        missing = [k for k in ("what", "why", "how_to_check") if not str(s.get(k, "")).strip()]
        if missing:
            problems.append(f"unverified_scope 第 {i} 項缺少：{', '.join(missing)}")
    return problems


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        problems = check(json.load(f))
    for p in problems:
        print(f"✗ {p}")
    if not problems:
        print("✓ 回報格式符合 R8")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
