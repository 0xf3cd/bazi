# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from importlib import import_module
from typing import Any

import pytest

from api_contract import BASES, DECLARED_MEMBERS


@pytest.mark.parametrize('qualified', [
  pytest.param(owner, marks=pytest.mark.input_contract(owner, 'from_str'))
  for owner, bases in BASES.items()
  if owner in DECLARED_MEMBERS and any(base in ('BaziEnum', 'IndexedBaziEnum') for base in bases)
])
def test_enum_strings_reject_wrong_inputs(qualified: str) -> None:
  module, name = qualified.rsplit('.', 1)
  enum: Any = getattr(import_module(module), name)
  with pytest.raises(TypeError, match='Expected str'):
    enum.from_str(None)
  with pytest.raises(ValueError):
    enum.from_str('not-a-member')
