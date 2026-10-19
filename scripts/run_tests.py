import sys
import unittest

suite = unittest.defaultTestLoader.discover('tests', pattern='test*.py')

count = suite.countTestCases()
print(f"Discovered {count} test cases.")

if count == 0:
    print("No test cases found. Exiting.")
    sys.exit(1)

result = unittest.TextTestRunner(verbosity=2).run(suite)
