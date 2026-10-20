# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from pathlib import Path

import pytest

from bazi.context_matching import ContextResult, RelationshipProfile
from bazi.transits import TransitKind

from flat_runner import MATCH_ARGS, run_cli


# #233 婚恋判据 CLI: guard matrix and legal combinations.

PALACE = 'editorial.spouse_palace_xingchong.v1'
TOUGAN = 'editorial.spouse_star_tougan.v1'

REL_BASE = ('--match-context', PALACE, '--birth-time', '2000-01-01 12:00', '--gender', 'male',
            '--observation-scope', 'natal')
REL_TRANSIT_BASE = ('--match-context', TOUGAN, '--birth-time', '2000-01-01 12:00', '--gender', 'male',
                    '--observation-scope', 'natal_and_transits')


@pytest.mark.parametrize('args', [
  ('--observation-scope', 'natal_and_transits'),
  ('--transit-entry', 'at_year'),
  ('--gz-month', '辰'),
  ('--solar-date', '2024-04-10'),
  ('--solar-moment', '2024-04-10T12:00:00'),
  ('--transit-kinds', 'liunian'),
])
def test_relationship_inputs_need_match_context(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, *args)
  assert result.returncode == 2 and 'Matching inputs require --match-context' in result.stderr
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('extra', [
  ('--query-knowledge',),
  ('--seed', '7'),
  ('--export-knowledge-json', 'k.json'),
])
def test_relationship_cannot_combine_modes(tmp_path: Path, extra: tuple[str, ...]) -> None:
  output = tmp_path / 'match.json'
  result = run_cli(tmp_path, *REL_BASE, '--transit-kinds', 'liunian', '--observation-scope', 'natal_and_transits', *extra, '--export-context-json', str(output))
  assert result.returncode == 2 and 'error:' in result.stderr
  assert not output.exists()


@pytest.mark.parametrize('extra', [
  ('--transit-entry', 'at_year'),
  ('--gz-month', '辰'),
  ('--solar-date', '2024-04-10'),
  ('--solar-moment', '2024-04-10T12:00:00'),
  ('--transit-kinds', 'liunian'),
])
def test_context_criteria_reject_new_flags(tmp_path: Path, extra: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, *MATCH_ARGS, *extra)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert list(tmp_path.iterdir()) == []


def test_context_scope_rejects_natal_transits(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *MATCH_ARGS, '--observation-scope', 'natal_and_transits')
  assert result.returncode == 2 and 'error:' in result.stderr


def test_relationship_rejects_natal_liunian(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *REL_BASE, '--observation-scope', 'natal_and_liunian')
  assert result.returncode == 2 and 'error:' in result.stderr


@pytest.mark.parametrize('extra', [
  ('--ganzhi-year', '2024'), ('--gz-month', '辰'), ('--solar-date', '2024-04-10'),
  ('--solar-moment', '2024-04-10T12:00:00'), ('--transit-kinds', 'liunian'),
  ('--transit-entry', 'at_year'),
])
def test_relationship_natal_rejects_transits(tmp_path: Path, extra: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, *REL_BASE, *extra)
  assert result.returncode == 2 and 'error:' in result.stderr


def test_natal_transits_requires_kinds(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE)
  assert result.returncode == 2 and 'error:' in result.stderr


@pytest.mark.parametrize('args, error', [
  ('--ganzhi-year', 'bad'), ('--gz-month', '子丑'), ('--gz-month', 'YOU'),
  ('--solar-date', '2024-04-10T12:00:00'), ('--solar-date', '20240410'),
  ('--solar-moment', '2024-04-10 12:00:00'), ('--solar-moment', '2024-04-10T12:00:00.25'),
  ('--solar-moment', '2024-04-10T12:00:00+08:00'),
])
def test_coordinate_values_must_be_canonical(tmp_path: Path, args: tuple[str, ...], error: str) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-entry', 'at_date', '--transit-kinds', 'liunian', *args)
  assert result.returncode == 2 and 'error:' in result.stderr


@pytest.mark.parametrize('entry_args', [
  ('--transit-entry', 'at_year', '--gz-month', '辰'),
  ('--transit-entry', 'at_year', '--solar-date', '2024-04-10'),
  ('--transit-entry', 'at_year', '--solar-moment', '2024-04-10T12:00:00'),
  ('--transit-entry', 'at_month', '--ganzhi-year', '2024'),
  ('--transit-entry', 'at_month', '--gz-month', '辰'),
  ('--transit-entry', 'at_date', '--ganzhi-year', '2024'),
  ('--transit-entry', 'at_date', '--gz-month', '辰'),
  ('--transit-entry', 'at_moment', '--ganzhi-year', '2024'),
  ('--transit-entry', 'at_moment', '--solar-date', '2024-04-10'),
])
def test_entry_fields_are_mutually_exclusive(tmp_path: Path, entry_args: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian', *entry_args)
  assert result.returncode == 2 and 'error:' in result.stderr


@pytest.mark.parametrize('entry_args, missing', [
  (('--transit-entry', 'at_year'), '--ganzhi-year'),
  (('--transit-entry', 'at_month', '--ganzhi-year', '2024'), '--gz-month'),
  (('--transit-entry', 'at_month', '--gz-month', '辰'), '--ganzhi-year'),
  (('--transit-entry', 'at_date'), '--solar-date'),
  (('--transit-entry', 'at_moment'), '--solar-moment'),
])
def test_entry_fields_are_required(tmp_path: Path, entry_args: tuple[str, ...], missing: str) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian', *entry_args)
  assert result.returncode == 2 and 'error:' in result.stderr, missing


@pytest.mark.parametrize('entry_args, kinds', [
  (('--transit-entry', 'at_year', '--ganzhi-year', '2024'), 'liuyue'),
  (('--transit-entry', 'at_year', '--ganzhi-year', '2024'), 'liuri'),
  (('--transit-entry', 'at_month', '--ganzhi-year', '2024', '--gz-month', '辰'), 'xiaoyun,liuri'),
])
def test_kinds_must_be_within_entry_support(tmp_path: Path, entry_args: tuple[str, ...], kinds: str) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', kinds, *entry_args)
  assert result.returncode == 2 and 'error:' in result.stderr


@pytest.mark.parametrize('kinds', ['liunian,liunian', 'bogus', 'liunian,', ',liunian', ''])
def test_kinds_reject_duplicates_unknown_empty(tmp_path: Path, kinds: str) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', kinds,
                    '--transit-entry', 'at_year', '--ganzhi-year', '2024')
  assert result.returncode == 2 and 'error:' in result.stderr


def test_coordinate_fields_require_entry(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian', '--ganzhi-year', '2024')
  assert result.returncode == 2 and 'error:' in result.stderr


def test_kinds_without_coordinate_is_unknown(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian')
  assert result.returncode == 0, result.stderr
  assert '事实判别：UNKNOWN；missing_transit_coordinate' in result.stdout
  assert '请求种类=[liunian]；取得种类=[]；未取得种类=[liunian]' in result.stdout
  assert '关联参考' not in result.stdout


def test_unordered_kinds_are_normalized(tmp_path: Path) -> None:
  output = tmp_path / 'rel.json'
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian,dayun',
                    '--transit-entry', 'at_year', '--ganzhi-year', '2024',
                    '--export-context-json', str(output))
  assert result.returncode == 0, result.stderr
  data = json.loads(output.read_text(encoding='utf-8'))
  assert data['profile']['kinds'] == ['dayun', 'liunian']
  restored = ContextResult.from_json(output.read_text(encoding='utf-8'))
  assert isinstance(restored.profile, RelationshipProfile)
  assert restored.profile.kinds == (TransitKind.DAYUN, TransitKind.LIUNIAN)


@pytest.mark.parametrize('entry_args', [
  ('--transit-entry', 'at_year', '--ganzhi-year', '2024'),
  ('--transit-entry', 'at_month', '--ganzhi-year', '2024', '--gz-month', '辰'),
  ('--transit-entry', 'at_date', '--solar-date', '2024-04-10'),
  ('--transit-entry', 'at_moment', '--solar-moment', '2024-04-10T12:00:00'),
])
@pytest.mark.parametrize('flag', [(), ('--include-reference-only',)])
def test_legal_relationship_combinations(tmp_path: Path, entry_args: tuple[str, ...], flag: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian', *entry_args, *flag)
  assert result.returncode == 0, result.stderr
  assert '事实判别：' in result.stdout and '证据：原局内部；' in result.stdout
  assert '证据：原局×岁运；' in result.stdout and '证据：岁运内部；' in result.stdout
  # at_moment requires a HOUR/MINUTE natal chart; with DAY precision the unavailable entry is an EXIT 0 UNKNOWN, not an error.
  if entry_args[1] == 'at_moment':
    assert '事实判别：UNKNOWN；transit_unavailable' in result.stdout
  assert ('关联参考' in result.stdout) == bool(flag)
  if flag:
    assert '该判据的条件参考，不表示事实已成立或完整前提已满足' in result.stdout
