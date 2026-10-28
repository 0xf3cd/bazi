# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from pathlib import Path

import pytest

from cli_runner import GUANSHA, XINGCHONG, BIRTH, run_cli, prepare


@pytest.mark.parametrize('commands,markers,files,charts', [
  ([['chart', '--seed', '42']], ('random seed: 42\n',), 0, 1),
  ([['chart', '--seed', '3', '--count', '2']], ('random seed: 3\n',), 0, 2),
  ([['chart', '--birth-time', '2000-01-01 12:00', '--gender', 'female', '--precision', 'hour', '--include-reference-only', '--show-sources']], ('仅供参考', '来源：'), 0, 1),
  ([['chart', '--seed', '5', '--output-dir', 'out']], ('random seed: 5\n',), 1, 1),
  ([['chart', '--seed', '5', '--output-dir', 'out'], ['knowledge', '--export-knowledge-base', '--output-dir', 'out']], ('random seed: 5\n',), 21, 1),
  ([['chart', '--seed', '5', '--include-reference-only', '--show-sources', '--output-dir', 'out'],
    ['knowledge', '--export-knowledge-base', '--output-dir', 'out', '--include-reference-only', '--show-sources']], ('仅供参考', '来源：'), 21, 1),
  ([['chart', '--birth-time', '2000-01-01T12:00:00+08:00', '--gender', 'male', '--precision', 'minute', '--longitude', '120.0', '--civil-timezone=+08:00']], ('真太阳出生时刻',), 0, 1),
  ([['chart', '--birth-time', '2000-01-01T12:00:00-05:00', '--gender', 'female', '--precision', 'hour', '--longitude', '-75.0', '--civil-timezone=America/New_York']], ('真太阳出生时刻',), 0, 1),
  ([['knowledge', '--object', 'tiangan.ding', '--include-reference-only']], ('丁为阴火。', '仅供参考'), 0, 0),
  ([['knowledge', '--all']], ('比肩为与日主五行、阴阳皆相同者。',), 0, 0),
  ([['knowledge', '--validate-knowledge']], ('校验通过：',), 0, 0),
  ([['knowledge', '--object', 'tiangan.ding', '--knowledge-source', 'src.json']], ('丁为阴火。',), 0, 0),
  ([['match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal']], ('结构前提：SATISFIED',), 0, 0),
  ([['match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal_and_liunian', '--ganzhi-year', '2024', '--include-reference-only']], ('结构前提：SATISFIED', '仅供参考'), 0, 0),
  ([['match', XINGCHONG, *BIRTH, '--gender', 'female', '--observation-scope', 'natal_and_transits', '--ganzhi-year', '2024', '--transit-entry', 'at_month', '--gz-month', '午', '--transit-kinds', 'liuyue,liunian']], ('at_month', '2024'), 0, 0),
  ([['match', XINGCHONG, *BIRTH, '--gender', 'male', '--observation-scope', 'natal_and_transits', '--transit-entry', 'at_date', '--solar-date', '2024-04-10', '--transit-kinds', 'liuri']], ('at_date', '2024-04-10'), 0, 0),
])
def test_task_combinations_preserve_their_outputs(
  tmp_path: Path, commands: list[list[str]], markers: tuple[str, ...], files: int, charts: int,
) -> None:
  cwd = prepare(tmp_path)
  results = [run_cli(cwd, *tokens) for tokens in commands]
  assert all(result.returncode == 0 and result.stderr == '' for result in results), [result.stderr for result in results]
  stdout = ''.join(result.stdout for result in results)
  assert all(marker in stdout for marker in markers)
  outputs = [path for path in (cwd / 'out').rglob('*') if path.is_file()]
  assert len(outputs) == files and all(path.suffix == '.txt' for path in outputs)
  assert stdout.count('出生时间：') + stdout.count('民用出生时刻（固定出生地偏移）：') == charts
