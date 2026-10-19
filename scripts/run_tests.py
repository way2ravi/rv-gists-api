# Provides process exit codes and Python's built-in test framework.
import sys
import unittest
# Resolves paths relative to this script rather than the caller's directory.
from pathlib import Path

# The repository root is the parent of the scripts directory.
PROJECT_ROOT = Path(__file__).parent.parent

# Make project modules importable while unittest discovers tests.
sys.path.insert(0, str(PROJECT_ROOT))

if len(sys.argv) != 2 or sys.argv[1] not in ("unit", "integration"):
    print("Usage: python scripts/run_tests.py [unit|integration]")
    sys.exit(2)

test_type = sys.argv[1]
test_directory = PROJECT_ROOT / "tests" / test_type

# Load matching tests from the tests directory with the repository as package root.
suite = unittest.defaultTestLoader.discover(start_dir=str(test_directory), pattern='test*.py', top_level_dir=str(PROJECT_ROOT))

# Count discovered test cases and report the count before running them.
count = suite.countTestCases()
print(f"Discovered {count} {test_type} test cases", flush=True)

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