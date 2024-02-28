import os
import pytest

def run_tests() -> int:
  return pytest.main(['-x', os.path.dirname(os.path.realpath(__file__)), '-v'])

if __name__ == '__main__':
  run_tests()
