import os
import pytest
from typing import Optional

def run_tests(expression: Optional[str]) -> int:
  args: list[str] = [
    '-v',
    '-x', os.path.dirname(os.path.realpath(__file__)),
  ]
  if expression is not None:
    args.extend(['-k', expression])
  return pytest.main(args)
