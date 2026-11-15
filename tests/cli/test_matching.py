# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import inspect
import json
from pathlib import Path

import pytest

from bazi import cli
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase
from bazi.context_matching import NatalObservation, LiunianObservation, criteria, evaluate_context

from cli_runner import GUANSHA, MATCH_ARGS, MATCH_BIRTH, run_cli


def test_cli_filters_match_library_directories() -> None:
  parsers = cli._subcommand_parsers(cli._command_parser())
  actions = {action.dest: action for action in parsers['knowledge']._actions}
  matching = {action.dest: action for action in parsers['match']._actions}
  filters = {'subject', 'source_id', 'topic', 'viewpoint'}
  assert set(inspect.signature(KnowledgeBase.query).parameters) - {'self'} == filters
  assert set(inspect.signature(KnowledgeBase.search).parameters) - {'self', 'keyword'} == filters
  assert set(cli._LIST_DIMENSIONS.values()) == (filters - {'subject'}) | {'object_id'}
  for dimension, flag in {'object_id': '--object', 'source_id': '--source', 'topic': '--topic', 'viewpoint': '--viewpoint'}.items():
    assert actions[dimension].option_strings == [flag]
  assert set(matching['observation_scope'].choices or ()) == {scope for info in criteria().values() for scope in info.scopes}
  assert set(matching['transit_entry'].choices or ()) == {entry for info in criteria().values() for entry in info.transit_entries}
  actual_flags = {flag for action in matching.values() for flag in action.option_strings}
  for info in criteria().values():
    for names in info.transit_entries.values():
      assert all(cli._COORDINATE_FLAGS[name] in actual_flags for name in names)


@pytest.mark.parametrize('criterion_id', [
  GUANSHA, 'tiangan.ding_weak_and_overcontrolled', 'tiangan.geng_regulated_transit',
  'shishen.pianyin_favorable_or_balanced', 'shishen.xiaoyin_duoshi',
])
@pytest.mark.parametrize('year', [None, 2024])
@pytest.mark.parametrize('reading', [False, True])
def test_match_output_agrees_with_library(
  tmp_path: Path, criterion_id: str, year: int | None, reading: bool,
) -> None:
  scope = ('--observation-scope', 'natal') if year is None else ('--observation-scope', 'natal_and_liunian', '--ganzhi-year', str(year))
  result = run_cli(tmp_path, 'match', criterion_id, *MATCH_BIRTH, *scope, *(('--knowledge',) if reading else ()))
  observation = NatalObservation() if year is None else LiunianObservation(year)
  expected = evaluate_context(BaziChart(Bazi.create('2000-01-03 12:00', 'female')), criterion_id=criterion_id, observation=observation)
  text = expected.render()
  if reading:
    kb = KnowledgeBase.load()
    text += ''.join('\n\n' + kb.render(kb.entry(identifier)) for identifier in expected.reference_ids)
  assert result.returncode == 0 and result.stdout == text + '\n', result.stderr
  assert '不表示现实事件成立' in text
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('mutation', ['premise', 'missing'])
def test_custom_source_keeps_criterion_verdict(tmp_path: Path, mutation: str) -> None:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  identifier = 'editorial.shishen.zhengguan.legal_trouble'
  if mutation == 'premise':
    next(e for e in data['entries'] if e['claim_id'] == identifier)['premise'] = '不同前提'
  else:
    data['entries'] = [e for e in data['entries'] if e['claim_id'] != identifier]
  source = tmp_path / 'edited.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  baseline = run_cli(tmp_path, *MATCH_ARGS)
  result = run_cli(tmp_path, *MATCH_ARGS, '--knowledge', '--knowledge-source', str(source))
  assert result.returncode == 0 and result.stdout.startswith(baseline.stdout.rstrip('\n'))
  assert '结构前提：SATISFIED；premise_satisfied' in result.stdout
  assert ('不同前提' if mutation == 'premise' else identifier + '：知识库未收录') in result.stdout
