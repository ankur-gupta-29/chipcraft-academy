"""
check_posts.py
Validates that every _posts/*.md file has required front matter fields
and that the filename date matches the front matter date.
Exits with code 1 if any post fails validation.
"""

import os
import re
import sys
from datetime import datetime

POSTS_DIR = "_posts"
REQUIRED_FIELDS = ["layout", "title", "description", "date", "category"]
FRONT_MATTER = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
FIELD = re.compile(r"^(\w+)\s*:\s*(.+)$", re.MULTILINE)
# Posts must be named YYYY-MM-DD-slug.md
FILENAME_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")


def parse_front_matter(content: str) -> dict:
    m = FRONT_MATTER.match(content)
    if not m:
        return {}
    return dict(FIELD.findall(m.group(1)))


def check_post(filename: str, path: str) -> list:
    """Returns a list of error strings (empty = pass)."""
    errors = []

    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Must start with front matter
    if not content.startswith("---"):
        errors.append("missing front matter (file must start with ---)")
        return errors

    fm = parse_front_matter(content)
    if not fm:
        errors.append("front matter block is empty or malformed")
        return errors

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"missing required field: '{field}'")

    # Date in front matter must be a real date
    if "date" in fm:
        date_str = fm["date"].strip().split()[0]  # handle "2026-05-12 10:00:00"
        try:
            fm_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            errors.append(f"'date' value '{date_str}' is not a valid YYYY-MM-DD date")
            fm_date = None

        # Filename date must match front matter date
        m = FILENAME_DATE.match(filename)
        if m and fm_date:
            file_date = datetime.strptime(m.group(1), "%Y-%m-%d")
            if file_date != fm_date:
                errors.append(
                    f"filename date {m.group(1)} does not match "
                    f"front matter date {date_str}"
                )

        # Warn if post is future-dated (Jekyll hides future posts by default)
        if fm_date and fm_date > datetime.utcnow():
            errors.append(
                f"post date {date_str} is in the future — "
                "Jekyll will hide this post until that date"
            )

    # Title must not be empty
    if "title" in fm and not fm["title"].strip().strip('"').strip("'"):
        errors.append("'title' is empty")

    return errors


def main() -> int:
    if not os.path.isdir(POSTS_DIR):
        print(f"❌ {POSTS_DIR}/ not found. Run from repo root.")
        return 1

    posts = sorted(f for f in os.listdir(POSTS_DIR) if f.endswith(".md"))
    print(f"Checking {len(posts)} post(s) in {POSTS_DIR}/\n")

    all_passed = True

    for post in posts:
        path = os.path.join(POSTS_DIR, post)
        errors = check_post(post, path)

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
    else:
        print("❌ Some posts have validation errors (see above).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
