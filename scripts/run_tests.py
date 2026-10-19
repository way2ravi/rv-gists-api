# Provides process exit codes and Python's built-in test framework.
import sys
import unittest
# Resolves paths relative to this script rather than the caller's directory.
from pathlib import Path

# The repository root is the parent of the scripts directory.
PROJECT_ROOT = Path(__file__).parent.parent

# Make project modules importable while unittest discovers tests.
sys.path.insert(0, str(PROJECT_ROOT))

# Load matching tests from the tests directory with the repository as package root.
suite = unittest.defaultTestLoader.discover(start_dir=str(PROJECT_ROOT / "tests"), pattern='test*.py', top_level_dir=str(PROJECT_ROOT))

# Count discovered test cases and report the count before running them.
count = suite.countTestCases()
print(f"Discovered {count} test cases", flush=True)

# Treat an empty discovery result as a configuration or naming error.
if count == 0:
    print("ERROR: No tests discovered")
    sys.exit(1)

# Run tests with detailed per-test output and retain the overall result.
result = unittest.TextTestRunner(
    verbosity=2
).run(suite)

# Return a successful process status only when every test passes.
sys.exit(0 if result.wasSuccessful() else 1)