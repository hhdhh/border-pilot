"""Quick check: which Python files fail to parse?"""
import ast
import sys
from pathlib import Path

ROOT = Path("/Users/kk/.openclaw/workspace/projects/border-pilot")
files = list(ROOT.rglob("*.py"))
files.sort()
failed = []
for f in files:
 try:
 ast.parse(f.read_text())
 except SyntaxError as e:
 failed.append((str(f), str(e).splitlines()[0] if e.text else ""))
for path, msg in failed:
 print(f"FAIL: {path}: {msg}")
print(f"\nTotal: {len(files)} files, {len(failed)} failed")
sys.exit(0 if not failed else1)
