# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
import json
import subprocess
import sys
from pathlib import Path

import pytest

from run_interpreter import interpret, main
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.interpreter import Interpreter
from bazi.knowledge import KnowledgeBase


KNOWLEDGE_BASE = KnowledgeBase.load()


@pytest.mark.parametrize('include_reference_only', [False, True])
def test_chart_display_uses_knowledge_topics_and_retains_selection(include_reference_only: bool) -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  text = interpret(chart, include_reference_only=include_reference_only)
  assert '定义：' + Interpreter.interpret_tiangan(chart.bazi.day_master)['general'][0] in text
  assert '原局中，劫财有' in text
  assert '当劫财状态不好时' not in text
  assert '能量状态佳' not in text and 'in_good_status' not in text
  assert ('仅供参考' in text) is include_reference_only
  assert ('前提待梳理' in text) is include_reference_only


def test_empty_knowledge_projection_keeps_chart_counts(monkeypatch: pytest.MonkeyPatch) -> None:
  empty = KnowledgeBase.from_json(KNOWLEDGE_BASE.export_json(()))
  monkeypatch.setattr(KnowledgeBase, 'load', staticmethod(lambda path=None: empty))
  text = interpret(BaziChart(Bazi.create('2000-01-01 12:00', 'male')))
  assert '原局中，劫财有' in text
  assert '定义：' not in text and '仅供参考' not in text


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
  assert '命盘适用性未判断' in result.stdout
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
  assert '命盘适用性未判断' in text
  assert '来源尚未核实' in text
  assert '来源：' not in text


def _run_guarded_script(
  script: Path,
  cwd: Path,
  args: tuple[str, ...],
) -> subprocess.CompletedProcess[str]:
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
    # PyPy FileIO reports closefd rather than OS flags when a mode is present.
    writable = (
      any(char in mode for char in 'wax+')
      if mode is not None
      else bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
    )
    if writable:
      raise PermissionError('Unexpected default file export')
  if event in ('os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.truncate'):
    raise PermissionError('Unexpected default filesystem change')

sys.addaudithook(deny_writes)
runpy.run_path(script, run_name='__main__')
'''
  return subprocess.run(
    [sys.executable, '-B', '-c', guard, str(script), *args],
    cwd=cwd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
  )


@pytest.mark.parametrize(('args', 'writes'), [
  ((), False),
  (('--seed', '42'), False),
  (('--output-dir', 'exported'), True),
  (('--export-knowledge-base',), True),
])
def test_default_cli_rejects_all_filesystem_writes(
  tmp_path: Path,
  args: tuple[str, ...],
  writes: bool,
) -> None:
  result = _run_guarded_script(
    Path(__file__).parents[1] / 'run_interpreter.py',
    tmp_path,
    args,
  )
  if writes:
    assert result.returncode == 2
    assert 'Unexpected default' in result.stderr
    assert not any(path.is_file() for path in tmp_path.rglob('*'))
  else:
    assert result.returncode == 0, result.stderr
    assert result.stdout.count('出生时间：') == 1
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('mode', ['w', 'a', 'x', 'r+'])
def test_write_guard_checks_high_level_modes_without_directory_operations(
  mode: str,
  tmp_path: Path,
) -> None:
  target = tmp_path / 'target.txt'
  target.write_text('existing data', encoding='utf-8')
  script = tmp_path / 'probe.py'
  script.write_text(
    f"open('target.txt', {mode!r}, encoding='utf-8')\n",
    encoding='utf-8',
  )
  result = _run_guarded_script(script, tmp_path, ())
  assert result.returncode != 0
  assert 'Unexpected default file export' in result.stderr
  assert target.read_text(encoding='utf-8') == 'existing data'


def test_reference_claims_have_distinct_lines_without_source_blocks() -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  result = interpret(chart, include_reference_only=True)
  general = Interpreter.query_tiangan(chart.bazi.day_master, include_reference_only=True)['general']
  assert len(general) > 1
  lines = result.splitlines()
  assert f'定义：{general[0].text}' in lines
  assert any(general[1].text in line and '仅供参考' in line for line in lines)
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
  assert '命盘适用性未判断' in result.stdout
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


def test_batch_generation_is_interleaved_with_rendering(
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  events: list[str] = []
  bazi = Bazi.create('2000-01-01 12:00', 'male')

  def generate() -> Bazi:
    events.append('generate')
    return bazi

  def render(chart: BaziChart, **kwargs: object) -> str:
    events.append('render')
    return 'chart'

  monkeypatch.setattr(Bazi, 'random', staticmethod(generate))
  monkeypatch.setitem(main.__globals__, '_chart_text', render)
  assert main(['--count', '3']) == 0
  assert events == ['generate', 'render', 'generate', 'render', 'generate', 'render']
  assert capsys.readouterr().out == 'chart\nchart\nchart\n'


def test_knowledge_query_runs_without_birth_input_or_filesystem_writes(tmp_path: Path) -> None:
  result = _run_cli(
    tmp_path, '--query-knowledge', '--object', 'tiangan.ding', '--topic', '历史象',
    '--source', 'yuanhai_ziping_stem_symbols_p70', '--include-reference-only',
  )
  assert result.returncode == 0, result.stderr
  assert 'tiangan.ding.lamp_symbol' in result.stdout
  assert '丁火有烛灯之象。' in result.stdout and 'p. 70' in result.stdout
  assert '支持范围：' in result.stdout and '局限：' in result.stdout
  assert '出生时间：' not in result.stdout
  assert '丁为阴火。' not in result.stdout
  assert list(tmp_path.iterdir()) == []
  guarded = _run_guarded_script(
    Path(__file__).parents[1] / 'run_interpreter.py', tmp_path,
    ('--query-knowledge', '--object', 'tiangan.ding'),
  )
  assert guarded.returncode == 0, guarded.stderr


def test_manual_context_preserves_undefined_and_external_premises(tmp_path: Path) -> None:
  result = _run_cli(
    tmp_path, '--query-knowledge', '--object', 'tiangan.geng',
    '--context', 'tiangan.geng_regulated_transit', '--topic', '性格',
    '--applicability', 'described', '--time-scope', '行运', '--include-reference-only',
  )
  assert result.returncode == 0, result.stderr
  for text in ('人工给定情境', '命盘适用性未判断', '后天有教养', '盘外前提', '有制有化尚未定义', '来源尚未核实'):
    assert text in result.stdout
  assert '出生时间：' not in result.stdout


def test_knowledge_default_and_known_empty_queries(tmp_path: Path) -> None:
  default = _run_cli(tmp_path, '--query-knowledge', '--object', 'tiangan.ding')
  assert default.returncode == 0
  assert '丁为阴火。' in default.stdout and '烛灯' not in default.stdout
  empty = _run_cli(tmp_path, '--query-knowledge', '--object', 'wuxing.mu')
  assert empty.returncode == 0 and empty.stdout == '无匹配条目。\n'
  variant = _run_cli(
    tmp_path, '--query-knowledge', '--object', 'shensha.guoyin',
    '--viewpoint', 'WUXING_JINGJI', '--include-reference-only',
  )
  assert variant.returncode == 0 and '#194' in variant.stdout
  assert 'shensha.guoyin.modern' not in variant.stdout


def test_knowledge_edit_validate_export_reload_cycle(tmp_path: Path) -> None:
  data = json.loads(KNOWLEDGE_BASE.export_json())
  record = next(entry for entry in data['entries'] if entry['claim_id'] == 'tiangan.ding.lamp_symbol')
  record['limits'] = ['本次编辑的限度。']
  source, exported, complete = (tmp_path / name for name in ('source.json', 'selection.json', 'complete.json'))
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  query = _run_cli(
    tmp_path, '--knowledge-source', str(source), '--validate-knowledge', '--query-knowledge',
    '--object', 'tiangan.ding', '--topic', '历史象', '--include-reference-only',
    '--export-knowledge-json', str(exported),
  )
  assert query.returncode == 0, query.stderr
  assert '校验通过：295 条目，9 来源见证，5 情境。' in query.stdout
  assert '本次编辑的限度。' in query.stdout
  restored = KnowledgeBase.load(exported)
  assert tuple(restored.entries) == ('tiangan.ding.lamp_symbol',)
  assert restored.sources == KNOWLEDGE_BASE.sources
  again = _run_cli(tmp_path, '--query-knowledge', '--knowledge-source', str(exported), '--include-reference-only')
  assert again.returncode == 0 and '本次编辑的限度。' in again.stdout and 'p. 70' in again.stdout
  full = _run_cli(tmp_path, '--export-knowledge-json', str(complete))
  assert full.returncode == 0 and '出生时间：' not in full.stdout
  assert KnowledgeBase.load(complete).entries == KNOWLEDGE_BASE.entries


@pytest.mark.parametrize('args', [
  ('--query-knowledge', '--birth-time', '2000-01-01 12:00', '--gender', 'male'),
  ('--query-knowledge', '--seed', '42'), ('--query-knowledge', '--count', '1'),
  ('--validate-knowledge', '--export-knowledge-base'), ('--query-knowledge', '--output-dir', 'output'),
  ('--object', 'tiangan.ding'), ('--knowledge-source', 'source.json'),
  ('--validate-knowledge', '--topic', '历史象'), ('--query-knowledge', '--object', 'typo'),
  ('--query-knowledge', '--context', 'typo'), ('--query-knowledge', '--applicability', 'typo'),
  ('--validate-knowledge', '--knowledge-source', 'missing.json'),
])
def test_knowledge_bad_inputs_do_not_create_exports(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = _run_cli(tmp_path, *args)
  assert result.returncode == 2
  assert 'error:' in result.stderr and 'Traceback' not in result.stderr
  assert list(tmp_path.iterdir()) == []


def test_knowledge_validation_rejects_corrupt_source_before_export(tmp_path: Path) -> None:
  source = tmp_path / 'corrupt.json'
  source.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
  result = _run_cli(tmp_path, '--validate-knowledge', '--knowledge-source', str(source), '--export-knowledge-json', str(tmp_path / 'out.json'))
  assert result.returncode == 2 and 'Duplicate JSON key' in result.stderr
  assert not (tmp_path / 'out.json').exists()


def test_validation_reads_the_edited_bundled_source_at_call_time(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  import bazi.knowledge as module

  (tmp_path / 'knowledge_data.json').write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
  monkeypatch.setattr(module, '__file__', str(tmp_path / 'knowledge.py'))
  with pytest.raises(SystemExit) as caught:
    main(['--validate-knowledge'])
  assert caught.value.code == 2
  assert 'Duplicate JSON key' in capsys.readouterr().err


def test_knowledge_export_cannot_truncate_its_editing_source(tmp_path: Path) -> None:
  source = tmp_path / 'source.json'
  source.write_text(KNOWLEDGE_BASE.export_json(), encoding='utf-8')
  before = source.read_bytes()
  for target in (source, tmp_path / 'hardlink.json'):
    if target != source:
      target.hardlink_to(source)
    result = _run_cli(
      tmp_path, '--knowledge-source', str(source), '--query-knowledge', '--object', 'tiangan.ding',
      '--export-knowledge-json', str(target),
    )
    assert result.returncode == 2 and 'overwrite the editing source' in result.stderr
    assert source.read_bytes() == before


def test_knowledge_export_io_error_uses_cli_error_exit(tmp_path: Path) -> None:
  blocker = tmp_path / 'file'
  blocker.write_text('existing', encoding='utf-8')
  result = _run_cli(tmp_path, '--export-knowledge-json', str(blocker / 'out.json'))
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'Traceback' not in result.stderr and blocker.read_text(encoding='utf-8') == 'existing'
