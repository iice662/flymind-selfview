"""Publish the repository through the GitHub API (api.github.com works here; git push does not).

`git push` from this machine fails with HTTP 408 / connection resets, while `gh api` and
`gh release` calls go through.  This script therefore commits the key documents with the contents
API (one PUT per file), which makes the repository non-empty, and then attaches the 11 MB bundle -
the complete repository in one file - as a release asset, because GitHub refuses release assets on
an empty repository (HTTP 422 "Repository is empty").

    python tools/publish_via_api.py                 # do it
    python tools/publish_via_api.py --check         # show what would be uploaded
"""
import argparse
import base64
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "iice662/flymind-selfview"
FILES = [
    "README.md",
    "LICENSE",
    ".gitignore",
    "DATA-DICTIONARY.md",
    "reproduce.ps1",
    "results/CORRECTION.md",
    "results/PROVENANCE.md",
    "results/RECEPTIVE-FIELD-STATUS.md",
    "results/CLOSED-LOOP-PLAN.md",
    "paper/manuscript.md",
    "paper/tables.md",
    "paper/cover-letter.md",
    "paper/DECISIONS.md",
    "paper/figures.md",
    "paper/reporting-summary.md",
    "paper/AI-DISCLOSURE.md",
    "paper/supplementary-note-S1.md",
    "paper/supplementary-note-S2.md",
]
BUNDLE = os.path.join(ROOT, "flymind-selfview.bundle")


def gh(args, inp=None):
    p = subprocess.run(["gh"] + args, capture_output=True, text=True, input=inp,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="publish every git-tracked file, not just the key documents")
    a = ap.parse_args()

    global FILES
    if a.all:
        p = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        FILES = [f for f in p.stdout.split("\n") if f.strip()]

    total = 0
    for rel in FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print("  MISSING", rel)
            continue
        size = os.path.getsize(p)
        total += size
        print(f"  {size/1024:8.1f} kB  {rel}")
    print(f"  {total/1024/1024:.2f} MB in {len(FILES)} files; "
          f"bundle {os.path.getsize(BUNDLE)/1024/1024:.1f} MB" if os.path.exists(BUNDLE) else "")
    if a.check:
        return 0

    for rel in FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        content = base64.b64encode(open(p, "rb").read()).decode("ascii")
        payload = json.dumps({"message": f"Add {rel}", "content": content})
        rc, out = gh(["api", "--method", "PUT", f"repos/{REPO}/contents/{rel}", "--input", "-"],
                     inp=payload)
        ok = rc == 0 or "sha" in out
        print(("  ok   " if ok else "  FAIL ") + rel + ("" if ok else " :: " + out.strip()[:120]))

    if os.path.exists(BUNDLE):
        rc, out = gh(["release", "upload", "v1.0.0", BUNDLE, "--repo", REPO, "--clobber"])
        print(("  ok   " if rc == 0 else "  FAIL ") + "release asset flymind-selfview.bundle"
              + ("" if rc == 0 else " :: " + out.strip()[:160]))
    rc, out = gh(["repo", "view", REPO, "--json", "isEmpty,url,visibility"])
    print("  repo:", out.strip()[:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
