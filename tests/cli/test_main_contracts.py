# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import date, datetime
import errno
import os
from pathlib import Path

import pytest

from bazi import cli
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import (
  Observation, NatalObservation, LiunianObservation, TransitObservation,
  YearCoordinate, MonthCoordinate, DateCoordinate, MomentCoordinate, evaluate_context,
)
from bazi.defines import Dizhi
from bazi.knowledge import KnowledgeBase
from bazi.school import BaziConfig
from bazi.transits import TransitKind

from cli_runner import GUANSHA, XINGCHONG, MATCH_ARGS, MATCH_BIRTH


REL_NATAL = ('match', XINGCHONG, *MATCH_BIRTH, '--observation-scope', 'natal')
REL_TRANSITS = ('match', XINGCHONG, *MATCH_BIRTH, '--observation-scope', 'natal_and_transits')
MISSING_SOURCE = str(FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), 'missing.json'))


def _expect_error(capsys: pytest.CaptureFixture[str], args: tuple[str, ...], reason: str) -> None:
  with pytest.raises(SystemExit) as caught:
    cli.main(list(args))
  assert caught.value.code == 2
  captured = capsys.readouterr()
  assert captured.out == '' and captured.err.startswith(f'usage: bazi {args[0]} ')
  assert captured.err.split(': error:', 1)[1] == f' {reason}\n'
  assert 'Traceback' not in captured.err


@pytest.mark.parametrize('args,reason', [
  (('chart', '--count', '0'), '--count must be positive'),
  (('chart', '--birth-time', '2000-01-03 12:00'), '--birth-time and --gender must be supplied together'),
  (('chart', '--gender', 'female'), '--birth-time and --gender must be supplied together'),
  (('chart', *MATCH_BIRTH, '--seed', '42'), '--seed and multiple charts require random input'),
  (('chart', *MATCH_BIRTH, '--count', '2'), '--seed and multiple charts require random input'),
  (('chart', '--longitude', '120'), 'Location and precision flags require fixed birth input'),
  (('chart', '--precision', 'minute'), 'Location and precision flags require fixed birth input'),
  (('chart', '--civil-timezone=+08:00'), 'Location and precision flags require fixed birth input'),
  (('chart', '--birth-time', 'invalid', '--gender', 'female'), "Invalid isoformat string: 'invalid'"),
  (('chart', *MATCH_BIRTH, '--longitude', '0', '--precision', 'hour'), 'Longitude requires a timezone-aware birth_time.'),
  (('chart', *MATCH_BIRTH, '--civil-timezone=+08:00'), 'civil_timezone requires longitude.'),
  (('knowledge', '--object', 'typo'), 'Unknown object_id: typo'),
  (('knowledge', '--context', 'typo'), 'Unknown context_id: typo'),
  (('knowledge', '--object', 'tiangan.ding', '--knowledge-source', 'missing.json'), MISSING_SOURCE),
  ((*MATCH_ARGS, '--knowledge-source', 'missing.json'), MISSING_SOURCE),
  ((*MATCH_ARGS, '--birth-time', 'invalid'), "Invalid isoformat string: 'invalid'"),
  ((*MATCH_ARGS, '--transit-entry', 'at_year'), 'Context criteria cannot combine transit entry, coordinate or kind inputs'),
  ((*MATCH_ARGS, '--observation-scope', 'natal_and_transits'), 'Unsupported value: natal_and_transits'),
  ((*MATCH_ARGS, '--ganzhi-year', '2024'), 'Natal scope cannot include a transit coordinate'),
  ((*REL_NATAL, '--observation-scope', 'natal_and_liunian'), 'Unsupported value: natal_and_liunian'),
  ((*REL_NATAL, '--ganzhi-year', '2024'), 'Transit coordinates require --transit-entry'),
  ((*REL_NATAL, '--transit-kinds', 'liunian'), 'Natal scope cannot include transit inputs'),
  ((*REL_NATAL, '--transit-entry', 'at_year', '--ganzhi-year', '2024'), 'Natal scope cannot include transit inputs'),
  (REL_TRANSITS, 'natal_and_transits requires explicit transit kinds'),
  ((*REL_TRANSITS, '--transit-entry', 'at_year', '--transit-kinds', 'liunian'), 'Missing coordinate field for at_year: ganzhi_year'),
  ((*REL_TRANSITS, '--transit-entry', 'at_year', '--ganzhi-year', '2024', '--gz-month', '辰', '--transit-kinds', 'liunian'),
   'Unexpected coordinate field for at_year: ganzhi_month'),
  ((*REL_TRANSITS, '--transit-kinds', 'liunian,liunian'), 'Duplicate transit kinds: liunian,liunian'),
  ((*REL_TRANSITS, '--transit-kinds', 'bogus'), 'Unsupported transit kind: bogus'),
  ((*REL_TRANSITS, '--transit-kinds', 'liunian,'), 'Unsupported transit kind: '),
  ((*REL_TRANSITS, '--gz-month', 'YOU'), "argument --gz-month: 'YOU' is not a valid Dizhi"),
  ((*REL_TRANSITS, '--solar-date', 'bad'), "argument --solar-date: Invalid isoformat string: 'bad'"),
  ((*REL_TRANSITS, '--solar-date', '20240410'), 'argument --solar-date: Expected canonical ISO date: 20240410'),
  ((*REL_TRANSITS, '--solar-moment', 'bad'), "argument --solar-moment: Invalid isoformat string: 'bad'"),
  ((*REL_TRANSITS, '--solar-moment', '2024-04-10 12:00:00'),
   'argument --solar-moment: Expected canonical naive moment: 2024-04-10 12:00:00'),
  ((*REL_TRANSITS, '--solar-moment', '2024-04-10T12:00:00+08:00'),
   'argument --solar-moment: Expected canonical naive moment: 2024-04-10T12:00:00+08:00'),
  (('chart', '--civil-timezone', 'Not/A_Zone'), "argument --civil-timezone: 'No time zone found with key Not/A_Zone'"),
])
def test_invalid_main_inputs_are_read_only(
  monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
  args: tuple[str, ...], reason: str,
) -> None:
  monkeypatch.chdir(tmp_path)
  _expect_error(capsys, args, reason)
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('task,error_type', [
  ('chart', TypeError), ('chart', ValueError),
  ('knowledge', OSError), ('knowledge', TypeError), ('knowledge', ValueError),
  ('match', OSError), ('match', TypeError), ('match', ValueError),
])
def test_library_failures_become_cli_errors(
  monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
  task: str, error_type: type[Exception],
) -> None:
  reason = f'Library boundary failure: {error_type.__name__}'

  def fail(*args: object, **kwargs: object) -> None:
    raise error_type(reason)

  monkeypatch.chdir(tmp_path)
  args: tuple[str, ...]
  if task == 'knowledge':
    monkeypatch.setattr(KnowledgeBase, 'load', staticmethod(fail))
    args = ('knowledge', '--object', 'tiangan.ding')
  else:
    monkeypatch.setattr(Bazi, 'create', staticmethod(fail))
    args = ('chart', *MATCH_BIRTH) if task == 'chart' else MATCH_ARGS
  _expect_error(capsys, args, reason)
  assert list(tmp_path.iterdir()) == []


def test_corrupt_query_source_is_not_modified(
  monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
  monkeypatch.chdir(tmp_path)
  source = tmp_path / 'source.json'
  original = b'{"schema_version":1,"schema_version":1}'
  source.write_bytes(original)
  _expect_error(capsys, ('knowledge', '--object', 'tiangan.ding', '--knowledge-source', 'source.json'),
                'Duplicate JSON key: schema_version')
  assert set(tmp_path.iterdir()) == {source} and source.read_bytes() == original


@pytest.mark.parametrize('criterion_id,precision,args,observation', [
  (GUANSHA, 'day', ('--observation-scope', 'natal_and_liunian', '--ganzhi-year', '2024'), LiunianObservation(2024)),
  (GUANSHA, 'day', ('--observation-scope', 'natal_and_liunian'), LiunianObservation()),
  (XINGCHONG, 'day', ('--observation-scope', 'natal'), NatalObservation()),
  (XINGCHONG, 'day', ('--observation-scope', 'natal_and_transits', '--transit-kinds', 'liunian'),
   TransitObservation((TransitKind.LIUNIAN,))),
  (XINGCHONG, 'day', ('--observation-scope', 'natal_and_transits', '--transit-entry', 'at_year',
    '--ganzhi-year', '2024', '--transit-kinds', 'liunian,dayun'),
   TransitObservation((TransitKind.DAYUN, TransitKind.LIUNIAN), YearCoordinate(2024))),
  (XINGCHONG, 'day', ('--observation-scope', 'natal_and_transits', '--transit-entry', 'at_month',
    '--ganzhi-year', '2024', '--gz-month', '午', '--transit-kinds', 'liuyue,liunian'),
   TransitObservation((TransitKind.LIUNIAN, TransitKind.LIUYUE), MonthCoordinate(2024, Dizhi.午))),
  (XINGCHONG, 'day', ('--observation-scope', 'natal_and_transits', '--transit-entry', 'at_date',
    '--solar-date', '2024-04-10', '--transit-kinds', 'liuri'),
   TransitObservation((TransitKind.LIURI,), DateCoordinate(date(2024, 4, 10)))),
  (XINGCHONG, 'minute', ('--observation-scope', 'natal_and_transits', '--transit-entry', 'at_moment',
    '--solar-moment', '2024-04-10T12:00:00', '--transit-kinds', 'liunian'),
   TransitObservation((TransitKind.LIUNIAN,), MomentCoordinate(datetime(2024, 4, 10, 12)))),
])
@pytest.mark.parametrize('reference', [False, True])
def test_match_main_preserves_domain_requests(
  monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
  criterion_id: str, precision: str, args: tuple[str, ...], observation: Observation, reference: bool,
) -> None:
  monkeypatch.chdir(tmp_path)
  chart = BaziChart(Bazi.create('2000-01-03 12:00', 'female', BaziConfig.from_values(precision=precision)))
  expected = evaluate_context(chart, criterion_id=criterion_id, observation=observation, include_reference_only=reference)
  argv = ['match', criterion_id, *MATCH_BIRTH, '--precision', precision, *args,
          *(['--include-reference-only'] if reference else [])]
  original = list(argv)
  assert cli.main(argv) == 0 and argv == original
  captured = capsys.readouterr()
  assert captured.err == '' and captured.out == expected.render() + '\n'
  assert list(tmp_path.iterdir()) == []


def test_naive_offset_parser_result_is_rejected(
  monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
  calls: list[str] = []

  class NaiveOffsetParser:
    @staticmethod
    def fromisoformat(value: str) -> datetime:
      calls.append(value)
      return datetime(2000, 1, 1)

  monkeypatch.chdir(tmp_path)
  monkeypatch.setattr(cli, 'datetime', NaiveOffsetParser)
  _expect_error(capsys, ('chart', '--civil-timezone=+08:00'), 'argument --civil-timezone: Expected fixed UTC offset')
  assert calls == ['2000-01-01T00:00:00+08:00']
  assert list(tmp_path.iterdir()) == []
