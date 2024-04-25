import os
import pytest
from typing import Optional

def run_hkodata_tests(expression: Optional[str] = None) -> int:
  args: list[str] = [
    os.path.dirname(os.path.realpath(__file__)),
    '-v',
    '-x', 
  ]
  if expression is not None:
    args.extend(['-k', expression])
  return pytest.main(args)
