"""
check_posts.py
Validates front matter in every _posts/*.md file:
  - Required fields present
  - Date is valid YYYY-MM-DD
  - Filename date matches front matter date
  - Post is not future-dated (Jekyll hides those by default)
Exits with code 1 if any post fails.
"""

import os
import re
import sys
from datetime import datetime, timezone

POSTS_DIR = "_posts"
REQUIRED_FIELDS = ["layout", "title", "description", "date", "category"]
FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
FIELD_RE        = re.compile(r"^(\w+)\s*:\s*(.+)$", re.MULTILINE)
FILENAME_DATE   = re.compile(r"^(\d{4}-\d{2}-\d{2})-")


def parse_front_matter(content: str) -> dict:
    m = FRONT_MATTER_RE.match(content)
    if not m:
        return {}
    return dict(FIELD_RE.findall(m.group(1)))


def check_post(filename: str, path: str) -> list:
    errors = []

    with open(path, encoding="utf-8-sig") as f:   # utf-8-sig strips BOM if present
        content = f.read()

    if not content.startswith("---"):
        return ["missing front matter block (file must start with ---)"]

    fm = parse_front_matter(content)
    if not fm:
        return ["front matter block is empty or malformed"]

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"missing required field: '{field}'")

    # Validate date field
    fm_date = None
    if "date" in fm:
        date_str = fm["date"].strip().split()[0]
        try:
            fm_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            errors.append(f"'date' value '{date_str}' is not a valid YYYY-MM-DD date")

        # Filename date must match front matter date
        m = FILENAME_DATE.match(filename)
        if m and fm_date:
            file_date = datetime.strptime(m.group(1), "%Y-%m-%d")
            if file_date != fm_date:
                errors.append(
                    f"filename date ({m.group(1)}) does not match "
                    f"front matter date ({date_str})"
                )

        # Future-dated posts are hidden by Jekyll by default
        if fm_date:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if fm_date.date() > now.date():
                errors.append(
                    f"post date {date_str} is in the future — "
                    "Jekyll will hide this post (set 'future: true' in _config.yml to override)"
                )

    # Title must not be empty
    if "title" in fm:
        title = fm["title"].strip().strip('"').strip("'")
        if not title:
            errors.append("'title' field is empty")

    return errors


def main() -> int:
    if not os.path.isdir(POSTS_DIR):
        print(f"❌ '{POSTS_DIR}/' not found — run from repo root.")
        return 1

    posts = sorted(f for f in os.listdir(POSTS_DIR) if f.endswith(".md"))
    print(f"Checking {len(posts)} post(s) in {POSTS_DIR}/\n")

    all_passed = True

    for post in posts:
        errors = check_post(post, os.path.join(POSTS_DIR, post))
        if errors:
            print(f"  ❌  {post}")
            for e in errors:
                print(f"      • {e}")
            all_passed = False
        else:
            print(f"  ✅  {post}")

    print()
    if all_passed:
        print("✅ All posts passed front matter validation.")
        return 0

    print("❌ Some posts failed validation (see above).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
