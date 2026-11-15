# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import random
import re
from pathlib import Path
from typing import Any

import pytest

from bazi import cli
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.chart_text import basic_text
from bazi.defines import Shishen, Tiangan
from bazi.knowledge import KnowledgeBase

from cli_runner import run_cli, MATCH_BIRTH


def test_chart_default_does_not_load_knowledge(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
  def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError('Default chart must not load knowledge')
  monkeypatch.setattr(KnowledgeBase, 'load', forbidden)
  assert cli.main(['chart', *MATCH_BIRTH]) == 0
  text = capsys.readouterr().out
  chart = BaziChart(Bazi.create('2000-01-03 12:00', 'female'))
  assert re.sub(r'\x1b\[[0-9;]*m', '', text) == basic_text(chart) + '\n'
  assert '占比' in text and '来源：' not in text and '\x1b[' in text


@pytest.mark.parametrize('sources', [False, True])
def test_chart_knowledge_deduplicates(sources: bool) -> None:
  chart = BaziChart(Bazi.create('2000-01-03 12:00', 'female'))
  kb = KnowledgeBase.load()
  text = cli._chart_knowledge(chart, kb, show_sources=sources)
  subjects: list[Tiangan | Shishen] = [
    chart.bazi.day_master,
    *(ss for ss in Shishen if any(ss in (pair.tiangan, pair.dizhi) for pair in chart.shishen)),
  ]
  expected = list(dict.fromkeys(entry.claim_id for subject in subjects for entry in kb.query(subject)))
  assert re.findall(r'^条目：(.*)$', text, re.MULTILINE) == expected
  for claim_id in expected:
    entry = kb.entry(claim_id)
    assert entry.text in text and entry.premise in text
    assert all(limit in text for limit in entry.limits)
  assert '【日主：' in text and '【十神：' in text and '命盘适用性未判断' in text
  assert ('引文／记录：' in text) is sources
  assert '出处未核' in text and '来源：' in text


def test_missing_objects_and_empty_entries() -> None:
  chart = BaziChart(Bazi.create('2000-01-03 12:00', 'female'))
  assert '知识库未收录该对象' in cli._chart_knowledge(chart, KnowledgeBase((), (), ()))
  kb = KnowledgeBase.load()
  assert '无相关条目' in cli._chart_knowledge(chart, KnowledgeBase(tuple(kb.objects.values()), (), ()))


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('located', [False, True])
@pytest.mark.parametrize('reading', [False, True])
def test_saved_txt_equals_complete_display(tmp_path: Path, optimized: bool, located: bool, reading: bool) -> None:
  birth = '2024-01-01T12:00:00+14:00' if located else '2024-01-01T12:00:00'
  location = ('--longitude', '-157.4') if located else ()
  flags = ('--knowledge', '--show-sources') if reading else ()
  result = run_cli(
    tmp_path, 'chart', '--birth-time', birth, '--gender', '女', '--precision', '分',
    *location, *flags, '--transits', '--relationship', '--output', 'chart.txt', optimized=optimized,
  )
  assert result.returncode == 0, result.stderr
  assert (tmp_path / 'chart.txt').read_text(encoding='utf-8') == re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)


@pytest.mark.parametrize('seed', [0, 42, -17])
def test_seed_replays_one_chart(seed: int, capsys: pytest.CaptureFixture[str]) -> None:
  state = random.getstate()
  chart = BaziChart(Bazi.random(rng=random.Random(seed)))
  assert cli.main(['chart', '--seed', str(seed)]) == 0
  assert capsys.readouterr().out == f'random seed: {seed}\n{cli._get_basic_info(chart)}\n'
  assert random.getstate() == state


def test_random_seed_is_saved(tmp_path: Path) -> None:
  first = run_cli(tmp_path, 'chart', '--output', 'chart.txt')
  assert first.returncode == 0
  seed = first.stdout.splitlines()[0].split(': ')[1]
  second = run_cli(tmp_path, 'chart', '--seed', seed)
  assert first.stdout == second.stdout
  assert (tmp_path / 'chart.txt').read_text(encoding='utf-8').startswith(f'random seed: {seed}\n')


@pytest.mark.parametrize('task', ['chart', 'match'])
def test_reading_options_need_explicit_read(tmp_path: Path, task: str) -> None:
  args = () if task == 'chart' else ('editorial.guansha_coexistence.v1', *MATCH_BIRTH, '--observation-scope', 'natal')
  for flags in (('--knowledge-source', 'missing.json'), ('--show-sources',)):
    result = run_cli(tmp_path, task, *args, *flags)
    assert result.returncode == 2 and 'require --knowledge' in result.stderr
    assert result.stdout == ''
