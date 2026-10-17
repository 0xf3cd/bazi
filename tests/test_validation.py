# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import pytest

from bazi._validation import _text, _choice, _tuple, _pairs, _mapping


def test_shared_validation_preserves_success_values_and_messages() -> None:
  _text('value')
  _text('   ', empty=True)
  _choice('value', ('value',))
  _tuple(('value',), str)
  _tuple((True,), int)
  assert _pairs([('a', 1), ('b', 2)]) == {'a': 1, 'b': 2}
  original = {'a': 1}
  assert _mapping(original, ('a',)) is original
  with pytest.raises(TypeError, match="^Expected str, got <class 'int'>$"):
    _text(1)
  with pytest.raises(ValueError, match='^Expected non-empty text$'):
    _text('   ')
  with pytest.raises(TypeError, match="^Expected str, got <class 'int'>$"):
    _choice(1, ('value',))
  with pytest.raises(ValueError, match='^Unsupported value: other$'):
    _choice('other', ('value',))
  with pytest.raises(TypeError, match="^Expected tuple, got <class 'list'>$"):
    _tuple(['value'], str)
  with pytest.raises(TypeError, match="^Expected str, got <class 'int'>$"):
    _tuple((1,), str)
  with pytest.raises(ValueError, match='^Expected non-empty text$'):
    _tuple(('',), str)
  with pytest.raises(ValueError, match='^Duplicate JSON key: a$'):
    _pairs([('a', 1), ('a', 2)])
  with pytest.raises(TypeError, match="^Expected JSON object, got <class 'list'>$"):
    _mapping([], ())
  with pytest.raises(ValueError, match="^JSON fields differ: .*a.*$"):
    _mapping({'a': 1}, ())
