import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = BACKEND_ROOT / 'test'
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(BACKEND_ROOT / 'src'))
sys.path.insert(0, str(TEST_ROOT))

from support import init_firebase as init_firebase


def run_tests(test_names=None):
    loader = unittest.TestLoader()
    if test_names:
        suite = loader.loadTestsFromNames(test_names)
    else:
        suite = loader.discover(str(TEST_ROOT), pattern='test_*.py')

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == '__main__':
    run_tests(sys.argv[1:])
