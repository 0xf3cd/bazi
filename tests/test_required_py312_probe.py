# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import sys


def test_required_py312_check_blocks_merge() -> None:
  assert sys.version_info[:2] != (3, 12), 'Intentional Python 3.12 failure: never merge this probe'
