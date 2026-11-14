"""check.py: the repo's one-command check (tests + text lint). The pre-commit hook runs it.

Runs every tests/test_*.py with unittest (stdlib only, so a fresh clone needs nothing installed).
Tests that need the ROM skip themselves when rom/ is missing. Exit code is the gate.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        import lint
        lint_rc = lint.main()
    except ImportError as e:   # keystone/pillow missing: the VWF tests skip too
        print(f"lint skipped: {e}")
        lint_rc = 0
    return 0 if result.wasSuccessful() and lint_rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
