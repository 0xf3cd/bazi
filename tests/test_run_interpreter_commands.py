# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_run_interpreter_commands.py

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import get_args

import pytest

import run_interpreter
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextProfile, ObservationScope, TransitEntry, criteria, evaluate_context
from bazi.knowledge import Applicability, DEFAULT_SOURCE_PATH, KnowledgeBase
from run_interpreter import _COMMANDS, _LIST_DIMENSIONS, _command_parser, _subcommand_parsers, main


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'run_interpreter.py'
GUANSHA = 'editorial.guansha_coexistence.v1'
XINGCHONG = 'editorial.spouse_palace_xingchong.v1'
BIRTH = ('--birth-time', '2000-01-03 12:00')


def _run(cwd: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, str(SCRIPT), *args],
    cwd=cwd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
    env=None if env is None else {**os.environ, **env},
  )


def _prepare(cwd: Path) -> Path:
  cwd.mkdir(parents=True, exist_ok=True)
  shutil.copyfile(DEFAULT_SOURCE_PATH, cwd / 'src.json')
  return cwd


def _outputs(cwd: Path) -> dict[str, bytes]:
  out = cwd / 'out'
  return {path.relative_to(cwd).as_posix(): path.read_bytes() for path in sorted(out.rglob('*')) if path.is_file()} if out.exists() else {}


def _hint_commands(stderr: str) -> list[list[str]]:
  lines = [line for line in stderr.splitlines() if line.startswith('提示：')]
  assert len(lines) == 1, stderr
  commands = lines[0].split('请改用：', 1)[1].split(' && ')
  parsed = [shlex.split(command) for command in commands]
  assert all(tokens[:2] == ['python', 'run_interpreter.py'] for tokens in parsed)
  return [tokens[2:] for tokens in parsed]


# 旧平铺调用 -> 提示给出的等价新命令（去掉 python run_interpreter.py 前缀）。
LEGACY_CASES = [
  (('--seed', '42'), [['chart', '--seed', '42']]),
  (('--seed', '3', '--count', '2'), [['chart', '--seed', '3', '--count', '2']]),
  (
    ('--birth-time', '2000-01-01 12:00', '--gender', 'female', '--precision', 'hour', '--include-reference-only', '--show-sources'),
    [['chart', '--birth-time', '2000-01-01 12:00', '--gender', 'female', '--precision', 'hour', '--include-reference-only', '--show-sources']],
  ),
  (
    ('--birth-time', '2000-01-01 12:00', '--gender', 'male', '--export-chart-json', 'out/c.json'),
    [['chart', '--birth-time', '2000-01-01 12:00', '--gender', 'male', '--export-chart-json', 'out/c.json']],
  ),
  (('--seed', '5', '--output-dir', 'out'), [['chart', '--seed', '5', '--output-dir', 'out']]),
  (
    ('--seed', '5', '--output-dir', 'out', '--export-knowledge-base'),
    [['chart', '--seed', '5', '--output-dir', 'out'], ['knowledge', '--export-knowledge-base', '--output-dir', 'out']],
  ),
  (
    ('--birth-time', '2000-01-01T12:00:00+08:00', '--gender', 'male', '--precision', 'minute', '--longitude', '120', '--civil-timezone=+08:00'),
    [['chart', '--birth-time', '2000-01-01T12:00:00+08:00', '--gender', 'male', '--precision', 'minute', '--longitude', '120.0', '--civil-timezone=+08:00']],
  ),
  (
    ('--birth-time', '2000-01-01T12:00:00-05:00', '--gender', 'female', '--precision', 'hour', '--longitude', '-75', '--civil-timezone', 'America/New_York'),
    [['chart', '--birth-time', '2000-01-01T12:00:00-05:00', '--gender', 'female', '--precision', 'hour', '--longitude', '-75.0', '--civil-timezone=America/New_York']],
  ),
  (
    ('--query-knowledge', '--object', 'tiangan.ding', '--include-reference-only'),
    [['knowledge', '--object', 'tiangan.ding', '--include-reference-only']],
  ),
  (('--query-knowledge',), [['knowledge', '--all']]),
  (('--validate-knowledge',), [['knowledge', '--validate-knowledge']]),
  (
    ('--query-knowledge', '--topic', '定义', '--applicability', 'unconditional', '--export-knowledge-json', 'out/k.json'),
    [['knowledge', '--topic', '定义', '--applicability', 'unconditional', '--export-knowledge-json', 'out/k.json']],
  ),
  (('--export-knowledge-json', 'out/all.json'), [['knowledge', '--export-knowledge-json', 'out/all.json']]),
  (
    ('--query-knowledge', '--object', 'tiangan.ding', '--knowledge-source', 'src.json'),
    [['knowledge', '--object', 'tiangan.ding', '--knowledge-source', 'src.json']],
  ),
  (
    ('--match-context', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal', '--export-context-json', 'out/m.json'),
    [['match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal', '--export-context-json', 'out/m.json']],
  ),
  (
    ('--match-context', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal_and_liunian', '--ganzhi-year', '2024', '--include-reference-only'),
    [['match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal_and_liunian', '--ganzhi-year', '2024', '--include-reference-only']],
  ),
  (
    ('--match-context', XINGCHONG, *BIRTH, '--gender', 'female', '--observation-scope', 'natal_and_transits', '--transit-entry', 'at_month', '--ganzhi-year', '2024', '--gz-month', '午', '--transit-kinds', 'liuyue,liunian'),
    [['match', XINGCHONG, *BIRTH, '--gender', 'female', '--observation-scope', 'natal_and_transits', '--ganzhi-year', '2024', '--transit-entry', 'at_month', '--gz-month', '午', '--transit-kinds', 'liuyue,liunian']],
  ),
  (
    ('--match-context', XINGCHONG, *BIRTH, '--gender', 'male', '--observation-scope', 'natal_and_transits', '--transit-entry', 'at_date', '--solar-date', '2024-04-10', '--transit-kinds', 'liuri'),
    [['match', XINGCHONG, *BIRTH, '--gender', 'male', '--observation-scope', 'natal_and_transits', '--transit-entry', 'at_date', '--solar-date', '2024-04-10', '--transit-kinds', 'liuri']],
  ),
]


@pytest.mark.parametrize('legacy, expected', LEGACY_CASES)
def test_legacy_call_hints_its_new_command(tmp_path: Path, legacy: tuple[str, ...], expected: list[list[str]]) -> None:
  result = _run(_prepare(tmp_path), *legacy)
  assert result.returncode == 0, result.stderr
  assert _hint_commands(result.stderr) == expected


@pytest.mark.parametrize('legacy, expected', LEGACY_CASES)
def test_hint_command_reproduces_the_legacy_run(tmp_path: Path, legacy: tuple[str, ...], expected: list[list[str]]) -> None:
  old = _run(_prepare(tmp_path / 'old'), *legacy)
  new_cwd = _prepare(tmp_path / 'new')
  runs = [_run(new_cwd, *tokens) for tokens in _hint_commands(old.stderr)]
  assert all(run.returncode == 0 and '提示：' not in run.stderr for run in runs), [run.stderr for run in runs]
  assert ''.join(run.stdout for run in runs) == old.stdout
  assert _outputs(new_cwd) == _outputs(tmp_path / 'old')
  if len(expected) == 2:
    assert (new_cwd / 'out' / 'knowledge_base' / 'tiangan').is_dir()


def test_legacy_failures_print_no_hint(tmp_path: Path) -> None:
  for args in (('--object', 'tiangan.ding'), ('--match-context', 'nope', *BIRTH), ('--count', '0')):
    result = _run(tmp_path, *args)
    assert result.returncode == 2 and '提示：' not in result.stderr


def test_legacy_hint_stays_readable_without_utf8(tmp_path: Path) -> None:
  result = _run(tmp_path, '--seed', '1', env={'PYTHONIOENCODING': 'ascii:backslashreplace'})
  assert result.returncode == 0
  assert 'python run_interpreter.py chart --seed 1' in result.stderr


def test_bare_call_still_draws_a_random_chart(tmp_path: Path) -> None:
  result = _run(tmp_path)
  assert result.returncode == 0 and result.stdout.startswith('random seed: ')
  assert _hint_commands(result.stderr) == [['chart']]


@pytest.mark.parametrize('args', [('--help',), ('-h',)])
def test_top_level_help_lists_three_tasks(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = _run(tmp_path, *args)
  assert result.returncode == 0 and '提示：' not in result.stderr
  for task in _COMMANDS:
    assert re.search(rf'^\s+{task}\s+\S', result.stdout, flags=re.MULTILINE)
    assert f'python run_interpreter.py {task}' in result.stdout


@pytest.mark.parametrize('task', _COMMANDS)
def test_task_help_fits_one_screen(tmp_path: Path, task: str) -> None:
  result = _run(tmp_path, task, '--help', env={'COLUMNS': '80'})
  assert result.returncode == 0
  assert len(result.stdout.splitlines()) <= 45, result.stdout
  assert '更多选项' in result.stdout


def test_chart_command_shows_a_seeded_chart(tmp_path: Path) -> None:
  first, second = (_run(tmp_path, 'chart', '--seed', '42') for _ in range(2))
  assert first.returncode == 0 and first.stdout == second.stdout and first.stderr == ''
  assert first.stdout.startswith('random seed: 42\n')
  assert list(tmp_path.iterdir()) == []


def test_chart_command_has_no_knowledge_options(tmp_path: Path) -> None:
  for flag in (('--object', 'tiangan.ding'), ('--export-knowledge-base',), ('--observation-scope', 'natal')):
    result = _run(tmp_path, 'chart', *flag)
    assert result.returncode == 2 and 'unrecognized arguments' in result.stderr


def test_bare_knowledge_gives_an_overview(tmp_path: Path) -> None:
  library = KnowledgeBase.load()
  result = _run(tmp_path, 'knowledge')
  assert result.returncode == 0 and result.stderr == ''
  assert f'{len(library.entries)} 条目（默认可见 {len(library.query())} 条' in result.stdout
  for flag, dimension in _LIST_DIMENSIONS.items():
    assert f'--{flag}：{len(library.filter_values(dimension))} 个值' in result.stdout
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('flag, dimension', sorted(_LIST_DIMENSIONS.items()))
def test_list_values_matches_the_library(tmp_path: Path, flag: str, dimension: str) -> None:
  result = _run(tmp_path, 'knowledge', '--list-values', flag)
  assert result.returncode == 0
  assert result.stdout.splitlines() == list(KnowledgeBase.load().filter_values(dimension))


def test_knowledge_filters_query_without_a_flag(tmp_path: Path) -> None:
  library = KnowledgeBase.load()
  result = _run(tmp_path, 'knowledge', '--object', 'tiangan.ding')
  expected = ''.join(library.render(entry) + '\n\n' for entry in library.query(object_id='tiangan.ding'))
  assert result.returncode == 0 and result.stdout == expected


def test_knowledge_all_lists_the_default_view(tmp_path: Path) -> None:
  library = KnowledgeBase.load()
  result = _run(tmp_path, 'knowledge', '--all')
  assert result.returncode == 0
  assert result.stdout.count('\n\n') >= len(library.query()) - 1 and library.query()[0].claim_id in result.stdout


def test_knowledge_exports_the_base_texts_only(tmp_path: Path) -> None:
  result = _run(tmp_path, 'knowledge', '--export-knowledge-base', '--output-dir', 'out')
  assert result.returncode == 0 and result.stdout == '' and result.stderr == ''
  assert len(list((tmp_path / 'out' / 'knowledge_base').rglob('*.txt'))) == 20
  assert not (tmp_path / 'out' / 'interpretation_examples').exists()


def test_knowledge_output_dir_needs_the_export(tmp_path: Path) -> None:
  result = _run(tmp_path, 'knowledge', '--output-dir', 'out')
  assert result.returncode == 2 and '--export-knowledge-base' in result.stderr
  assert list(tmp_path.iterdir()) == []


def test_knowledge_bad_values_exit_with_an_error(tmp_path: Path) -> None:
  for args in (('--list-values', 'nope'), ('--applicability', 'maybe'), ('--knowledge-source', 'missing.json')):
    result = _run(tmp_path, 'knowledge', *args)
    assert result.returncode == 2 and 'error:' in result.stderr and 'Traceback' not in result.stderr


def test_bare_match_lists_every_criterion(tmp_path: Path) -> None:
  result = _run(tmp_path, 'match')
  assert result.returncode == 0
  for criterion_id, info in criteria().items():
    assert criterion_id in result.stdout and info.definition in result.stdout


@pytest.mark.parametrize('criterion_id', sorted(criteria()))
def test_match_with_only_an_id_describes_it(tmp_path: Path, criterion_id: str) -> None:
  info = criteria()[criterion_id]
  result = _run(tmp_path, 'match', criterion_id)
  assert result.returncode == 0 and result.stderr == ''
  assert info.definition in result.stdout and f'match {criterion_id} --birth-time' in result.stdout
  assert all(scope in result.stdout for scope in info.scopes)
  assert all(f'--transit-entry {entry}' in result.stdout for entry in info.transit_entries)
  assert (f'性别门槛：{info.required_gender}' in result.stdout) == (info.required_gender is not None)
  assert list(tmp_path.iterdir()) == []


def test_match_unknown_id_points_to_the_list(tmp_path: Path) -> None:
  result = _run(tmp_path, 'match', 'nope')
  assert result.returncode == 2 and 'Unsupported' in result.stderr and 'match 可列出全部判据' in result.stderr


@pytest.mark.parametrize('given, missing', [
  (('--birth-time', '2000-01-03 12:00'), ('--gender', '--observation-scope')),
  (('--gender', 'female'), ('--birth-time', '--observation-scope')),
  (('--observation-scope', 'natal'), ('--birth-time', '--gender')),
  (('--include-reference-only',), ('--birth-time', '--gender', '--observation-scope')),
])
def test_match_names_every_missing_input(tmp_path: Path, given: tuple[str, ...], missing: tuple[str, ...]) -> None:
  result = _run(tmp_path, 'match', GUANSHA, *given)
  assert result.returncode == 2
  assert f'missing {" and ".join(missing)};' in result.stderr
  assert 'example: python run_interpreter.py match <判据ID> --birth-time' in result.stderr
  assert list(tmp_path.iterdir()) == []


def test_match_inputs_need_an_id(tmp_path: Path) -> None:
  result = _run(tmp_path, 'match', '--gender', 'female')
  assert result.returncode == 2 and 'criterion ID is required' in result.stderr


def test_match_new_form_equals_the_library(tmp_path: Path) -> None:
  result = _run(tmp_path, 'match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal')
  expected = evaluate_context(
    BaziChart(Bazi.create('2000-01-03 12:00', 'female')), criterion_id=GUANSHA, profile=ContextProfile('natal'),
  ).render()
  assert result.returncode == 0 and result.stdout == expected + '\n'


def test_match_keeps_the_input_validation(tmp_path: Path) -> None:
  for args in (
    ('--observation-scope', 'natal_and_transits'),
    ('--observation-scope', 'natal', '--transit-entry', 'at_year'),
  ):
    result = _run(tmp_path, 'match', GUANSHA, *BIRTH, '--gender', 'female', *args)
    assert result.returncode == 2 and 'error:' in result.stderr


def test_command_options_agree_with_library_directories() -> None:
  subparsers = _subcommand_parsers(_command_parser())
  assert tuple(subparsers) == _COMMANDS
  dests = {name: {action.dest: action for action in sub._actions} for name, sub in subparsers.items()}
  assert set(dests['knowledge']['applicability'].choices or ()) == set(get_args(Applicability))
  assert tuple(dests['knowledge']['list_values'].choices or ()) == tuple(_LIST_DIMENSIONS)
  scopes = tuple(dests['match']['observation_scope'].choices or ())
  assert scopes == (*get_args(ObservationScope), 'natal_and_transits')
  assert set(scopes) == {scope for info in criteria().values() for scope in info.scopes}
  entries = tuple(dests['match']['transit_entry'].choices or ())
  assert entries == get_args(TransitEntry)
  assert set(entries) == {entry for info in criteria().values() for entry in info.transit_entries}
  assert not {'object_id', 'observation_scope', 'export_knowledge_base'} & set(dests['chart'])
  assert not {'seed', 'object_id', 'export_chart_json'} & set(dests['match'])


# ---- 进程内：同一批分支再走一遍，便于对脚本做覆盖测量（根脚本不在库覆盖闸门内）。

def _call(monkeypatch: pytest.MonkeyPatch, cwd: Path, *args: str) -> int | str | None:
  monkeypatch.chdir(cwd)
  try:
    return main(list(args))
  except SystemExit as stop:
    return stop.code


def test_inprocess_commands_cover_every_branch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
  _prepare(tmp_path)
  cases: list[tuple[tuple[str, ...], int | None]] = [
    (('-h',), 0), (('chart', '--seed', '1'), 0), (('chart', '--seed', '1', '--output-dir', 'o1'), 0),
    (('knowledge',), 0), (('knowledge', '--list-values', 'topic'), 0), (('knowledge', '--all'), 0),
    (('knowledge', '--object', 'tiangan.ding', '--export-knowledge-json', 'o2/k.json'), 0),
    (('knowledge', '--validate-knowledge'), 0),
    (('knowledge', '--export-knowledge-base', '--output-dir', 'o3'), 0),
    (('knowledge', '--output-dir', 'o4'), 2), (('knowledge', '--knowledge-source', 'missing.json'), 2),
    (('knowledge', '--list-values', 'topic', '--knowledge-source', 'missing.json'), 2),
    (('match',), 0), (('match', GUANSHA), 0), (('match', XINGCHONG), 0), (('match', 'nope'), 2),
    (('match', GUANSHA, '--gender', 'female'), 2), (('match', '--gender', 'female'), 2),
    (('match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal'), 0),
    (('match', 'editorial.guansha_coexistence_female.v1'), 0),
    (('knowledge', '--export-knowledge-base', '--output-dir', 'src.json'), 2),
    (('--seed', '1'), 0), (('--query-knowledge', '--topic', '定义'), 0), (('--object', 'tiangan.ding'), 2),
    (('--seed', '1', '--output-dir', 'o5', '--export-knowledge-base'), 0),
    (('--match-context', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal'), 0),
    (('--birth-time', '2000-01-01T12:00:00+08:00', '--gender', 'male', '--precision', 'minute', '--longitude', '120', '--civil-timezone=+08:00'), 0),
  ]
  for args, code in cases:
    assert _call(monkeypatch, tmp_path, *args) in ((0, None) if code == 0 else (code,)), args
  assert (tmp_path / 'o3' / 'knowledge_base').is_dir() and (tmp_path / 'o1' / 'interpretation_examples').is_dir()
  assert '提示：' in capsys.readouterr().err


@pytest.mark.parametrize('zone, text', [('Asia/Shanghai', 'Asia/Shanghai'), ('+05:30', '+05:30'), ('-05:00', '-05:00'), ('+05:30:15', '+05:30:15')])
def test_zone_text_round_trips_both_forms(zone: str, text: str) -> None:
  assert run_interpreter._zone_text(run_interpreter._civil_timezone(zone)) == text


def test_option_renders_every_value_kind() -> None:
  from datetime import date, datetime
  assert run_interpreter._option('--x', None) == [] and run_interpreter._option('--x', False) == []
  assert run_interpreter._option('--x', True) == ['--x']
  assert run_interpreter._option('--x', date(2024, 4, 10)) == ['--x', '2024-04-10']
  assert run_interpreter._option('--x', datetime(2024, 4, 10, 12)) == ['--x', '2024-04-10T12:00:00']
  assert run_interpreter._option('--x', 120.0) == ['--x', '120.0']


# ---- 文档里的命令只解析、不执行：新形式才算数。

def _doc_commands(markdown: str) -> list[list[str]]:
  found: list[list[str]] = []
  for block in re.findall(r'```(?:sh|bash)\n(.*?)```', markdown, flags=re.DOTALL):
    text = re.sub(r'\\\n\s*', ' ', block)
    for line in text.splitlines():
      tokens = shlex.split(line)
      if 'run_interpreter.py' in tokens:
        found.append(tokens[tokens.index('run_interpreter.py') + 1:])
  return found


def _check_doc_command(tokens: list[str]) -> None:
  if not tokens or tokens[0] not in _COMMANDS:
    raise AssertionError(f'Not a subcommand form: {tokens}')
  _command_parser().parse_args(tokens)


DOC_FILES = ('README.md', 'docs/guides/knowledge.md', 'docs/guides/quickstart.md', 'docs/guides/integration.md',
             'docs/guides/configuration.md', 'docs/guides/relations-transits.md', 'CONTRIBUTING.md')


def test_documented_commands_parse_as_subcommands() -> None:
  commands = [tokens for name in DOC_FILES for tokens in _doc_commands((ROOT / name).read_text(encoding='utf-8'))]
  assert len(commands) >= 3
  for tokens in commands:
    _check_doc_command(tokens)


@pytest.mark.parametrize('block', [
  '```sh\npython run_interpreter.py --seed 1\n```',
  '```sh\npython run_interpreter.py chart --no-such-flag\n```',
  '```sh\npython run_interpreter.py chart --seed \\\n  one\n```',
  '```sh\npython run_interpreter.py\n```',
])
def test_doc_command_check_rejects_bad_examples(block: str) -> None:
  commands = _doc_commands(block)
  assert len(commands) == 1
  with pytest.raises((AssertionError, SystemExit)):
    _check_doc_command(commands[0])


def test_doc_command_check_accepts_a_good_example() -> None:
  commands = _doc_commands(f'```sh\npython run_interpreter.py \\\n  match {GUANSHA} \\\n  --birth-time "2000-01-01 12:00" --gender male --observation-scope natal\n```')
  assert commands[0][0] == 'match'
  _check_doc_command(commands[0])
