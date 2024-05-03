import os
import pytest
from typing import Optional

def run_bazi_tests(expression: Optional[str] = None, slow_tests: bool = False) -> int:
  args: list[str] = [
    os.path.dirname(os.path.realpath(__file__)),
    '-v',
    '-x',
  ]
  if expression is not None:
    args.extend(['-k', expression])
  if not slow_tests:
    args.extend(['-m', 'not slow'])
  return pytest.main(args)

def run_errorprone_bazi_tests(expression: Optional[str] = None, repeat: int = 3) -> int:
  args: list[str] = [
    os.path.dirname(os.path.realpath(__file__)),
    '-v',
    '-x',
    '-m', 'errorprone',
  ]

  if expression is not None:
    args.extend(['-k', expression])

  ret_code: int = 0
  for _ in range(repeat):
    ret_code |= pytest.main(args)
    if ret_code != 0:
      break

  return ret_code
