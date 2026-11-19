# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from bazi.context_matching import criteria
from bazi.knowledge import KnowledgeBase


def test_current_content_and_order() -> None:
  # This baseline protects content, including premises and source boundaries, independently of schema validity.
  expected = json.loads((Path(__file__).with_name('data') / 'knowledge_content.json').read_text(encoding='utf-8'))
  knowledge = KnowledgeBase.load()
  for name in ('objects', 'sources', 'entries'):
    records = getattr(knowledge, name)
    assert list(records) == [identifier for identifier, _ in expected[name]]
    for identifier, fingerprint in expected[name]:
      payload = json.dumps(asdict(records[identifier]), ensure_ascii=False, sort_keys=True).encode('utf-8')
      assert sha256(payload).hexdigest() == fingerprint, (name, identifier)


def test_declared_references_are_bundled() -> None:
  knowledge = KnowledgeBase.load()
  for info in criteria().values():
    assert set(info.claim_ids) <= knowledge.entries.keys(), info.criterion_id
