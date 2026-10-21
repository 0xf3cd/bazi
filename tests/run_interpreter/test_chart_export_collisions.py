# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
import json
from pathlib import Path

import pytest

from bazi.bazi_chart import BaziChart

from cli_runner import run_cli


def test_location_export_cannot_hit_knowledge(tmp_path: Path) -> None:
  source = Path(__file__).parents[2] / 'bazi/knowledge_data.json'
  alias = tmp_path / 'alias.json'
  alias.symlink_to(source)
  before = source.read_bytes()
  result = run_cli(tmp_path, 'chart', '--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'male',
                    '--longitude', '-157.4', '--precision', 'minute', '--export-chart-json', str(alias))
  assert result.returncode == 2 and 'overwrite' in result.stderr
  assert source.read_bytes() == before


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('located', [False, True])
def test_json_txt_collision_writes_nothing(tmp_path: Path, optimized: bool, located: bool) -> None:
  output = tmp_path / 'output'
  target = output / 'interpretation_examples' / '0.txt'
  birth = '2024-01-01T12:00:00+14:00' if located else '2024-01-01T12:00:00'
  location = ('--longitude', '-157.4') if located else ()
  result = run_cli(tmp_path, 'chart', '--birth-time', birth, '--gender', 'female', '--precision', 'minute',
                    *location, '--output-dir', str(output), '--export-chart-json', str(target), optimized=optimized)
  assert result.returncode == 2 and 'overlap generated TXT' in result.stderr
  assert '已导出命盘' not in result.stdout and not output.exists()


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('alias', ['direct', 'file-symlink', 'hardlink', 'directory-symlink'])
def test_json_collision_keeps_aliases(tmp_path: Path, optimized: bool, alias: str) -> None:
  output = tmp_path / 'output'
  txt = output / 'interpretation_examples' / '0.txt'
  txt.parent.mkdir(parents=True)
  txt.write_bytes(b'existing text must survive')
  target = txt
  if alias == 'file-symlink':
    target = tmp_path / 'chart.json'
    target.symlink_to(txt)
  elif alias == 'hardlink':
    target = tmp_path / 'chart.json'
    target.hardlink_to(txt)
  elif alias == 'directory-symlink':
    directory = tmp_path / 'output-alias'
    directory.symlink_to(output, target_is_directory=True)
    target = directory / 'interpretation_examples' / '0.txt'
  before = txt.read_bytes()
  result = run_cli(tmp_path, 'chart', '--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'female',
                    '--longitude', '-157.4', '--precision', 'minute', '--output-dir', str(output),
                    '--export-chart-json', str(target), optimized=optimized)
  assert result.returncode == 2 and 'overlap generated TXT' in result.stderr
  assert txt.read_bytes() == before and target.read_bytes() == before
  assert '已导出命盘' not in result.stdout


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('family,member', [('tiangan', '甲'), ('shishen', '比肩')])
def test_json_rejects_knowledge_txt_collision(tmp_path: Path, optimized: bool, family: str, member: str) -> None:
  output = tmp_path / 'output'
  target = output / 'knowledge_base' / family / f'{member}.txt'
  result = run_cli(tmp_path, 'knowledge',
                    '--output-dir', str(output), '--export-knowledge-base',
                    '--export-knowledge-json', str(target), optimized=optimized)
  assert result.returncode == 2 and 'overlap generated TXT' in result.stderr
  assert not output.exists() and '已导出知识' not in result.stdout


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('located', [False, True])
def test_distinct_json_txt_outputs_both_kept(tmp_path: Path, optimized: bool, located: bool) -> None:
  output = tmp_path / 'output'
  target = output / 'chart.json'
  birth = '2024-01-01T12:00:00+14:00' if located else '2024-01-01T12:00:00'
  location = ('--longitude', '-157.4') if located else ()
  result = run_cli(tmp_path, 'chart', '--birth-time', birth, '--gender', 'female', '--precision', 'minute',
                    *location, '--output-dir', str(output), '--export-chart-json', str(target), optimized=optimized)
  assert result.returncode == 0, result.stderr
  data = json.loads(target.read_text(encoding='utf-8'))
  assert BaziChart.from_json(data).json == data
  text = (output / 'interpretation_examples' / '0.txt').read_text(encoding='utf-8')
  displayed = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).split('已导出命盘：', 1)[0].removesuffix('\n')
  assert text == displayed and '已导出命盘' not in text
