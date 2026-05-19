"""
check_verilog.py
Extracts every ```verilog block from _posts/*.md.
For each post, all complete modules are compiled TOGETHER in one
iverilog call so cross-module instantiations resolve correctly.
Exits with code 1 if any post's Verilog fails syntax checking.
"""

import os
import re
import sys
import subprocess
import tempfile

POSTS_DIR = "_posts"
VERILOG_BLOCK = re.compile(r"```verilog\n(.*?)```", re.DOTALL)


def is_complete_module(code: str) -> bool:
    """True only for blocks that contain a full module definition."""
    return "module " in code and "endmodule" in code


def check_post_modules(post_name: str, blocks: list) -> bool:
    """
    Compile all complete modules from one post together in a single
    iverilog run so instantiated sub-modules are in scope.
    Returns True if clean, False on error.
    """
    complete = [(i, b) for i, b in enumerate(blocks, 1) if is_complete_module(b)]
    skipped  = len(blocks) - len(complete)

    if not complete:
        if blocks:
            print(f"  ⏭  {post_name}: {len(blocks)} snippet(s) — all skipped (no complete modules)")
        return True

    print(f"  Compiling {len(complete)} module(s) from [{post_name}]  "
          f"({skipped} snippet(s) skipped)")

    # Write every complete module to its own temp file
    tmpfiles = []
    try:
        for idx, code in complete:
            tf = tempfile.NamedTemporaryFile(
                suffix=".v", mode="w", delete=False,
                prefix=f"chipcraft_{idx}_"
            )
            tf.write(code)
            tf.close()
            tmpfiles.append((idx, tf.name))

        cmd = ["iverilog", "-g2012", "-t", "null"] + [f for _, f in tmpfiles]
        result = subprocess.run(cmd, capture_output=True, text=True)

    finally:
        for _, f in tmpfiles:
            if os.path.exists(f):
                os.unlink(f)

    if result.returncode != 0:
        # Replace temp paths with readable block labels in error output
        stderr = result.stderr
        for idx, tf in tmpfiles:
            stderr = stderr.replace(tf, f"<{post_name}:block{idx}>")
        print(f"  ❌  FAIL  [{post_name}]")
        for line in stderr.strip().splitlines():
            print(f"      {line}")
        return False

    print(f"  ✅  PASS  [{post_name}]")
    return True


def main() -> int:
    if not os.path.isdir(POSTS_DIR):
        print(f"❌ '{POSTS_DIR}/' not found — run this script from the repo root.")
        return 1

    posts = sorted(f for f in os.listdir(POSTS_DIR) if f.endswith(".md"))
    print(f"Scanning {len(posts)} post(s) in {POSTS_DIR}/\n")

    failed = []

    for post in posts:
        path = os.path.join(POSTS_DIR, post)
        with open(path, encoding="utf-8-sig") as f:   # utf-8-sig strips BOM if present
            content = f.read()

        blocks = VERILOG_BLOCK.findall(content)
        if not blocks:
            continue

        ok = check_post_modules(post, blocks)
        if not ok:
            failed.append(post)

    # ── Summary ───────────────────────────────────────────────
    print()
    print("=" * 60)
    if failed:
        print(f"❌ {len(failed)} post(s) failed Verilog syntax check:")
        for p in failed:
            print(f"   • {p}")
        return 1

    print(f"✅ All Verilog modules in {len(posts)} post(s) passed syntax check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
