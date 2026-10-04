# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
import subprocess
import sys
from pathlib import Path

import pytest

from run_interpreter import interpret, main
from bazi.common import frozendict
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Shishen, Tiangan
from bazi.descriptions import (
  ShishenDescription, TianganDescription, DescriptionClaim, DescriptionClaims,
  DescriptionOutput, DescriptionSource,
)
from bazi.interpreter import Interpreter


def _assert_headings(
  section: str,
  headings: tuple[tuple[str, list[str]], ...],
) -> None:
  for heading, descriptions in headings:
    assert (heading + '\n'.join(descriptions) in section) is bool(descriptions)
  present_headings = tuple(heading for heading, descriptions in headings if descriptions)
  positions = tuple(section.index(heading) for heading in present_headings)
  assert positions == tuple(sorted(positions))


def _shishen_from_section(section: str) -> Shishen:
  matching_shishens = tuple(
    shishen for shishen in Shishen
    if section.startswith(f'原局中，{shishen}有')
  )
  assert len(matching_shishens) == 1
  return matching_shishens[0]


@pytest.mark.parametrize(('tiangan_fields', 'shishen_fields'), [
  (
    {'general': ['日主解读。'], 'personality': []},
    {
      'general': [],
      'in_good_status': ['状态良好。'],
      'in_bad_status': [],
      'relationship': ['关系描述。'],
    },
  ),
  (
    {'general': [], 'personality': ['日主个性。']},
    {
      'general': ['十神解读。'],
      'in_good_status': [],
      'in_bad_status': ['状态不好。'],
      'relationship': [],
    },
  ),
  (
    {'general': ['日主解读。'], 'personality': ['日主个性。']},
    {
      'general': ['十神解读。'],
      'in_good_status': ['状态良好。'],
      'in_bad_status': ['状态不好。'],
      'relationship': ['关系描述。'],
    },
  ),
  (
    {'general': [], 'personality': []},
    {
      'general': ['十神解读。'],
      'in_good_status': ['状态良好。'],
      'in_bad_status': [],
      'relationship': [],
    },
  ),
  (
    {'general': [], 'personality': []},
    {
      'general': [],
      'in_good_status': [],
      'in_bad_status': [],
      'relationship': [],
    },
  ),
], ids=['alternating-a', 'alternating-b', 'all-content', 'leading-content', 'all-empty'])
def test_interpret_description_headings_follow_content(
  tiangan_fields: TianganDescription,
  shishen_fields: ShishenDescription,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))

  def claims(field: str, texts: list[str]) -> tuple[DescriptionClaim, ...]:
    return tuple(
      DescriptionClaim(
        f'test.{field}.{i}',
        text,
        (DescriptionSource.EDITORIAL,),
        'Test',
        (),
        DescriptionOutput.DEFAULT,
      )
      for i, text in enumerate(texts)
    )

  def tiangan_description(_: Tiangan, *, include_reference_only: bool = False) -> DescriptionClaims:
    return frozendict({
      'general': claims('general', tiangan_fields['general']),
      'personality': claims('personality', tiangan_fields['personality']),
    })

  def shishen_description(_: Shishen, *, include_reference_only: bool = False) -> DescriptionClaims:
    return frozendict({
      'general': claims('general', shishen_fields['general']),
      'in_good_status': claims('in_good_status', shishen_fields['in_good_status']),
      'in_bad_status': claims('in_bad_status', shishen_fields['in_bad_status']),
      'relationship': claims('relationship', shishen_fields['relationship']),
    })

  monkeypatch.setattr(
    Interpreter,
    'query_tiangan',
    staticmethod(tiangan_description),
  )
  monkeypatch.setattr(
    Interpreter,
    'query_shishen',
    staticmethod(shishen_description),
  )

  sections = interpret(chart).split('\n' + '-' * 60 + '\n')
  assert len(sections) > 3
  _, _, day_master_section, *shishen_sections = sections

  day_master_headings = (
    ('解读：', tiangan_fields['general']),
    ('日主的个性：', tiangan_fields['personality']),
  )
  _assert_headings(day_master_section, day_master_headings)

  for section in shishen_sections:
    shishen = _shishen_from_section(section)
    shishen_headings = (
      ('解读：', shishen_fields['general']),
      (f'{shishen}代表的特点：', shishen_fields['in_good_status']),
      (f'当{shishen}状态不好时，可能会有以下特点：', shishen_fields['in_bad_status']),
      (f'{shishen}的恋爱/交友观：', shishen_fields['relationship']),
    )
    _assert_headings(section, shishen_headings)


def test_interpret_real_descriptions_follow_content() -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  sections = interpret(chart).split('\n' + '-' * 60 + '\n')
  assert len(sections) > 3
  _, _, day_master_section, *shishen_sections = sections

  day_master_description = Interpreter.interpret_tiangan(chart.bazi.day_master)
  day_master_headings = (
    ('解读：', day_master_description['general']),
    ('日主的个性：', day_master_description['personality']),
  )
  _assert_headings(day_master_section, day_master_headings)

  rendered_shishens: set[Shishen] = set()
  for section in shishen_sections:
    shishen = _shishen_from_section(section)
    rendered_shishens.add(shishen)
    description = Interpreter.interpret_shishen(shishen)
    shishen_headings = (
      ('解读：', description['general']),
      (f'{shishen}代表的特点：', description['in_good_status']),
      (f'当{shishen}状态不好时，可能会有以下特点：', description['in_bad_status']),
      (f'{shishen}的恋爱/交友观：', description['relationship']),
    )
    _assert_headings(section, shishen_headings)

  assert Shishen.劫财 in rendered_shishens
  assert Interpreter.interpret_shishen(Shishen.劫财) == {
    'general': [],
    'in_good_status': [],
    'in_bad_status': [],
    'relationship': [],
  }


def _run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, str(Path(__file__).parents[1] / 'run_interpreter.py'), *args],
    cwd=cwd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
  )


def test_cli_help_and_seeded_default_are_read_only(tmp_path: Path) -> None:
  help_result = _run_cli(tmp_path, '--help')
  assert help_result.returncode == 0
  assert '--show-sources' in help_result.stdout
  first = _run_cli(tmp_path, '--seed', '42')
  second = _run_cli(tmp_path, '--seed', '42')
  assert first.returncode == second.returncode == 0
  assert first.stdout == second.stdout
  assert first.stdout.count('出生时间：') == 1
  assert '来源：' not in first.stdout
  assert list(tmp_path.iterdir()) == []


def test_cli_source_display_does_not_expand_reference_selection(tmp_path: Path) -> None:
  result = _run_cli(
    tmp_path, '--birth-time', '2000-01-01 12:00', '--gender', 'male', '--show-sources',
  )
  assert result.returncode == 0
  assert '出生时间：2000-01-01, 12:0' in result.stdout
  assert '来源：' in result.stdout
  assert '支持范围：' in result.stdout
  assert '局限：' in result.stdout
  assert '条目：tiangan.wu.definition；署名：《渊海子平》与《命理探源》天干定义' in result.stdout
  assert '仅供参考' not in result.stdout
  assert 'legacy.' not in result.stdout


def test_cli_reference_export_retains_unverified_and_unevaluated_states(tmp_path: Path) -> None:
  result = _run_cli(
    tmp_path,
    '--birth-time', '2000-01-01 12:00', '--gender', 'male',
    '--include-reference-only', '--show-sources',
    '--output-dir', str(tmp_path), '--export-knowledge-base',
  )
  assert result.returncode == 0
  assert '来源尚未核实' in result.stdout
  assert '适用条件需整盘判断，尚未判断' in result.stdout
  assert '仅供参考' in result.stdout
  saved = tmp_path / 'interpretation_examples' / '0.txt'
  assert saved.read_text(encoding='utf-8') == re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).removesuffix('\n')
  assert len(list((tmp_path / 'knowledge_base' / 'tiangan').glob('*.txt'))) == 10
  assert len(list((tmp_path / 'knowledge_base' / 'shishen').glob('*.txt'))) == 10
  ding = (tmp_path / 'knowledge_base' / 'tiangan' / '丁.txt').read_text(encoding='utf-8')
  assert '丁火有烛灯之象' in ding
  assert '《刻京台增补渊海子平大全》' in ding


def test_cli_exports_exact_displayed_chart_count(tmp_path: Path) -> None:
  result = _run_cli(tmp_path, '--seed', '42', '--count', '2', '--output-dir', str(tmp_path))
  assert result.returncode == 0
  assert result.stdout.count('出生时间：') == 2
  assert {p.name for p in (tmp_path / 'interpretation_examples').iterdir()} == {'0.txt', '1.txt'}
  assert not (tmp_path / 'knowledge_base').exists()


@pytest.mark.parametrize('args', [
  ('--birth-time', '2000-01-01 12:00'),
  ('--gender', 'male'),
  ('--gender', 'other'),
  ('--count', '0'),
  ('--count', '-1'),
  ('--count', 'invalid'),
  ('--birth-time', 'invalid', '--gender', 'male'),
  ('--birth-time', '2000-01-01 12:00', '--gender', 'male', '--seed', '42'),
  ('--birth-time', '2000-01-01 12:00', '--gender', 'male', '--count', '2'),
  ('--unknown',),
])
def test_cli_rejects_invalid_inputs_without_exports(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = _run_cli(tmp_path, *args)
  assert result.returncode == 2
  assert 'error:' in result.stderr
  assert not result.stdout
  assert list(tmp_path.iterdir()) == []


def test_source_and_reference_rendering_are_independent() -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  text = interpret(chart, include_reference_only=True)
  assert '仅供参考' in text
  assert '适用条件需整盘判断，尚未判断' in text
  assert '来源尚未核实' in text
  assert '来源：' not in text


@pytest.mark.parametrize('args', [(), ('--seed', '42')])
def test_default_cli_rejects_all_filesystem_writes(tmp_path: Path, args: tuple[str, ...]) -> None:
  script = Path(__file__).parents[1] / 'run_interpreter.py'
  guard = '''
import os
import runpy
import sys
from pathlib import Path

script = sys.argv[1]
sys.path.insert(0, str(Path(script).parent))
sys.argv = sys.argv[1:]

def deny_writes(event, args):
  if event == 'open':
    _, mode, flags = args
    if (mode and any(char in mode for char in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
      raise PermissionError('Unexpected default file export')
  if event in ('os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.truncate'):
    raise PermissionError('Unexpected default filesystem change')

sys.addaudithook(deny_writes)
runpy.run_path(script, run_name='__main__')
'''
  result = subprocess.run(
    [sys.executable, '-B', '-c', guard, str(script), *args],
    cwd=tmp_path,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
  )
  assert result.returncode == 0, result.stderr
  assert result.stdout.count('出生时间：') == 1
  assert list(tmp_path.iterdir()) == []


def test_reference_claims_have_distinct_lines_without_source_blocks() -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  result = interpret(chart, include_reference_only=True)
  general = Interpreter.query_tiangan(chart.bazi.day_master, include_reference_only=True)['general']
  assert len(general) > 1
  lines = result.splitlines()
  assert f'解读：{general[0].text}' in lines
  assert any(line.startswith(general[1].text) and '仅供参考' in line for line in lines)
  assert '来源：' not in result


def test_exports_retain_other_existing_files(tmp_path: Path) -> None:
  first = _run_cli(tmp_path, '--seed', '42', '--count', '2', '--output-dir', str(tmp_path))
  assert first.returncode == 0
  output = tmp_path / 'interpretation_examples'
  earlier = (output / '1.txt').read_bytes()
  (output / '0.txt').write_text('sentinel', encoding='utf-8')
  (output / 'notes.txt').write_text('personal notes', encoding='utf-8')
  second = _run_cli(tmp_path, '--seed', '42', '--output-dir', str(tmp_path))
  assert second.returncode == 0
  assert (output / '0.txt').read_text(encoding='utf-8') == re.sub(
    r'\x1b\[[0-9;]*m', '', second.stdout,
  ).removesuffix('\n')
  assert (output / '1.txt').read_bytes() == earlier
  assert (output / 'notes.txt').read_text(encoding='utf-8') == 'personal notes'


def test_bad_export_path_uses_cli_error_exit(tmp_path: Path) -> None:
  output = tmp_path / 'file'
  output.write_text('existing data', encoding='utf-8')
  result = _run_cli(tmp_path, '--seed', '42', '--output-dir', str(output))
  assert result.returncode == 2
  assert not result.stdout
  assert 'error:' in result.stderr
  assert 'Traceback' not in result.stderr
  assert output.read_text(encoding='utf-8') == 'existing data'


@pytest.mark.parametrize('error_type', [TypeError, ValueError, OSError])
def test_internal_rendering_errors_propagate(
  error_type: type[Exception],
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  error = error_type('Internal rendering failure')

  def broken_render(*args: object, **kwargs: object) -> str:
    raise error

  monkeypatch.setitem(main.__globals__, '_chart_text', broken_render)
  with pytest.raises(error_type, match='Internal rendering failure') as caught:
    main(['--birth-time', '2000-01-01 12:00', '--gender', 'male'])
  assert caught.value is error


@pytest.mark.parametrize('stage', ['directory', 'chart', 'knowledge'])
def test_export_io_failures_use_error_exit(
  stage: str,
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  def fail(*args: object, **kwargs: object) -> None:
    raise OSError('Export I/O failure')

  if stage == 'directory':
    monkeypatch.setattr(Path, 'mkdir', fail)
  elif stage == 'chart':
    monkeypatch.setitem(main.__globals__, '_write_chart', fail)
  else:
    monkeypatch.setitem(main.__globals__, 'save_knowledge_base', fail)

  with pytest.raises(SystemExit) as caught:
    main([
      '--birth-time', '2000-01-01 12:00', '--gender', 'male',
      '--output-dir', str(tmp_path), '--export-knowledge-base',
    ])
  assert caught.value.code == 2
  assert 'error: Export I/O failure' in capsys.readouterr().err


def test_cli_reference_only_without_source_display(tmp_path: Path) -> None:
  result = _run_cli(
    tmp_path,
    '--birth-time', '2000-01-01 12:00', '--gender', 'female', '--include-reference-only',
  )
  assert result.returncode == 0
  assert result.stdout.count('出生时间：') == 1
  assert '性别：female' in result.stdout
  assert '仅供参考' in result.stdout
  assert '适用条件需整盘判断，尚未判断' in result.stdout
  assert '来源尚未核实' in result.stdout
  assert '来源：' not in result.stdout
  assert '条目：' not in result.stdout
  assert list(tmp_path.iterdir()) == []


def test_knowledge_export_defaults_are_isolated(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  monkeypatch.setitem(main.__globals__, '_DEFAULT_OUTPUT_DIR', tmp_path)
  assert main([
    '--birth-time', '2000-01-01 12:00', '--gender', 'male', '--export-knowledge-base',
  ]) == 0
  assert not (tmp_path / 'interpretation_examples').exists()
  assert len(list((tmp_path / 'knowledge_base' / 'tiangan').glob('*.txt'))) == 10
  assert len(list((tmp_path / 'knowledge_base' / 'shishen').glob('*.txt'))) == 10
  ding = (tmp_path / 'knowledge_base' / 'tiangan' / '丁.txt').read_text(encoding='utf-8')
  assert '丁为阴火。' in ding
  assert '丁火有烛灯之象' not in ding
  assert '仅供参考' not in ding
  assert '来源：' not in ding


def test_print_errors_propagate(monkeypatch: pytest.MonkeyPatch) -> None:
  error = BrokenPipeError('Print failure')

  def fail(*args: object, **kwargs: object) -> None:
    raise error

  monkeypatch.setitem(main.__globals__, 'print', fail)
  with pytest.raises(BrokenPipeError) as caught:
    main(['--birth-time', '2000-01-01 12:00', '--gender', 'male'])
  assert caught.value is error
