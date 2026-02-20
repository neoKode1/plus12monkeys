#!/usr/bin/env python3
"""Helper script to check git state and commit+push W2-W8 changes."""
import subprocess, os, sys

REPO = '/Users/babypegasus/Desktop/prototypes/+12monkeys'
OUT = os.path.join(REPO, '_git_output.txt')
os.chdir(REPO)

lines = []
def log(msg):
    lines.append(msg)
    with open(OUT, 'w') as f:
        f.write('\n'.join(lines) + '\n')

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

log("=== GIT STATE CHECK ===")
head, _, _ = run(['git', 'rev-parse', 'HEAD'])
log(f"HEAD: {head}")
logr, _, _ = run(['git', 'log', '--oneline', '-5'])
log(f"LOG:\n{logr}")
status, _, _ = run(['git', 'status', '--porcelain'])
log(f"STATUS:\n{status if status else '(clean)'}")

if not status:
    log("Working tree clean, nothing to commit.")
    sys.exit(0)

log("\n--- Staging changes ---")
run(['git', 'add', '-A'])
run(['git', 'reset', 'HEAD', 'nanda-index'])
status2, _, _ = run(['git', 'status', '--porcelain'])
log(f"After staging:\n{status2}")

msg = "fix: resolve remaining warnings W2-W3, W5-W8"
log(f"\n--- Committing: {msg} ---")
out, err, rc = run(['git', 'commit', '-m', msg])
log(f"commit out: {out}")
log(f"commit err: {err}")
log(f"commit rc: {rc}")

if rc == 0:
    head2, _, _ = run(['git', 'rev-parse', 'HEAD'])
    log(f"New HEAD: {head2}")
    log("\n--- Pushing ---")
    out, err, rc = run(['git', 'push', 'origin', 'main'])
    log(f"push out: {out}")
    log(f"push err: {err}")
    log(f"push rc: {rc}")
else:
    log("Commit failed. Not pushing.")

