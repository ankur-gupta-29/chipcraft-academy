"""
check_verilog.py
Extracts every ```verilog code block from _posts/*.md and runs
iverilog syntax checking on any block that is a complete module.
Exits with code 1 if any complete module fails to parse.
"""

import os
import re
import sys
import subprocess
import tempfile

POSTS_DIR = "_posts"
# Matches ```verilog ... ``` (non-greedy, across lines)
VERILOG_BLOCK = re.compile(r"```verilog\n(.*?)```", re.DOTALL)


def is_complete_module(code: str) -> bool:
    """Only check blocks that are full module definitions."""
    return "module " in code and "endmodule" in code


def syntax_check(code: str, label: str) -> bool:
    """
    Write code to a temp file and run:
        iverilog -t null -Wall <file>
    Returns True if syntax is clean, False otherwise.
    Prints errors to stdout so they show in CI logs.
    """
    with tempfile.NamedTemporaryFile(
        suffix=".v", mode="w", delete=False, prefix="chipcraft_ci_"
    ) as f:
        f.write(code)
        tmp = f.name

    try:
        result = subprocess.run(
            ["iverilog", "-t", "null", "-Wall", tmp],
            capture_output=True,
            text=True,
        )
    finally:
        os.unlink(tmp)

    if result.returncode != 0:
        print(f"\n  ❌  FAIL  [{label}]")
        # Clean up temp path from error messages so output is readable
        stderr = result.stderr.replace(tmp, "<snippet>")
        for line in stderr.strip().splitlines():
            print(f"      {line}")
        return False

    print(f"  ✅  PASS  [{label}]")
    return True


def main() -> int:
    if not os.path.isdir(POSTS_DIR):
        print(f"❌ {POSTS_DIR}/ directory not found. Run from repo root.")
        return 1

    posts = sorted(
        f for f in os.listdir(POSTS_DIR) if f.endswith(".md")
    )

    total = 0
    passed = 0
    skipped = 0
    failed_labels = []

    print(f"Scanning {len(posts)} post(s) in {POSTS_DIR}/\n")

    for post in posts:
        path = os.path.join(POSTS_DIR, post)
        with open(path, encoding="utf-8") as f:
            content = f.read()

        blocks = VERILOG_BLOCK.findall(content)
        if not blocks:
            continue

        print(f"── {post}  ({len(blocks)} verilog block(s))")

        for i, block in enumerate(blocks, start=1):
            label = f"{post}:block{i}"

            if not is_complete_module(block):
                print(f"  ⏭  SKIP  [{label}]  (snippet — no module/endmodule)")
                skipped += 1
                continue

            total += 1
            ok = syntax_check(block, label)
            if ok:
                passed += 1
            else:
                failed_labels.append(label)

        print()

    # ── Summary ───────────────────────────────────────────────
    print("=" * 60)
    print(f"Verilog check complete")
    print(f"  Checked : {total}")
    print(f"  Passed  : {passed}")
    print(f"  Skipped : {skipped}  (incomplete snippets)")
    print(f"  Failed  : {len(failed_labels)}")

    if failed_labels:
        print("\nFailed blocks:")
        for label in failed_labels:
            print(f"  • {label}")
        return 1

    print("\n✅ All complete Verilog modules passed syntax check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
