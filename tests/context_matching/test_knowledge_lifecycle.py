# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from pathlib import Path
from typing import Any

import pytest

from bazi.knowledge import KnowledgeBase

from matching_samples import match, rel_match


@pytest.mark.parametrize('source_text', [None, '{', '{"entries": []}'])
def test_evaluation_never_reads_knowledge(
  source_text: str | None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
  source = tmp_path / 'knowledge.json'
  baseline = (match(), rel_match())
  if source_text is not None:
    source.write_text(source_text, encoding='utf-8')
  monkeypatch.setattr('bazi.knowledge.DEFAULT_SOURCE_PATH', source)
  def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError('Computation must not load or render knowledge')
  monkeypatch.setattr(KnowledgeBase, 'load', forbidden)
  monkeypatch.setattr(KnowledgeBase, 'render', forbidden)
  results = (match(), rel_match())
  for result, previous in zip(results, baseline, strict=True):
    assert result == previous and hash(result) == hash(previous)
    assert result.render() == previous.render()
    assert result.reference_ids
