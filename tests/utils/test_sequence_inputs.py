# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from collections.abc import Callable, Iterator, Sequence
from typing import NoReturn

import pytest

from bazi.defines import Tiangan, Dizhi, TianganRelation, DizhiRelation
from bazi.utils import tiangan_utils, dizhi_utils


@pytest.mark.parametrize('call', [
  pytest.param(lambda values: tiangan_utils.search(values, TianganRelation.合), id='tiangan-search'),
  pytest.param(tiangan_utils.discover, id='tiangan-discover'),
  pytest.param(lambda values: tiangan_utils.discover_mutual(values, []), id='tiangan-mutual-left'),
  pytest.param(lambda values: tiangan_utils.discover_mutual([], values), id='tiangan-mutual-right'),
  pytest.param(lambda values: dizhi_utils.search(values, DizhiRelation.六合), id='dizhi-search'),
  pytest.param(dizhi_utils.discover, id='dizhi-discover'),
  pytest.param(lambda values: dizhi_utils.discover_mutual(values, []), id='dizhi-mutual-left'),
  pytest.param(lambda values: dizhi_utils.discover_mutual([], values), id='dizhi-mutual-right'),
])
@pytest.mark.parametrize('kind', ['empty-iterator', 'iterator', 'generator', 'set', 'mapping', 'scalar', 'string'])
def test_non_sequences_fail_before_iteration(call: Callable[..., object], kind: str) -> None:
  consumed: list[bool] = []
  def generate() -> Iterator[Tiangan]:
    consumed.append(True)
    yield Tiangan.甲
  values: object = {
    'empty-iterator': iter(()),
    'iterator': iter((Tiangan.甲,)),
    'generator': generate(),
    'set': {Tiangan.甲},
    'mapping': {Tiangan.甲: Tiangan.己},
    'scalar': 42,
    'string': '甲',
  }[kind]
  with pytest.raises(TypeError):
    call(values)
  assert not consumed
  if kind == 'iterator':
    assert tuple(values) == (Tiangan.甲,) # type: ignore[arg-type]


@pytest.mark.parametrize('call, value', [(tiangan_utils.discover_mutual, Tiangan.甲), (dizhi_utils.discover_mutual, Dizhi.辰)])
@pytest.mark.parametrize('side', [0, 1])
def test_mutual_checks_both_containers_before_either_is_traversed(call: Callable[..., object], value: object, side: int) -> None:
  class UnreadSequence(Sequence[object]):
    def __len__(self) -> int:
      raise RuntimeError('Sequence traversed before container checks')
    def __getitem__(self, index: int | slice) -> NoReturn:
      raise RuntimeError('Sequence traversed before container checks')
  arguments = [UnreadSequence(), iter((value,))]
  if side:
    arguments.reverse()
  with pytest.raises(TypeError, match='Sequence'):
    call(*arguments)


@pytest.mark.parametrize('container', [list, tuple])
def test_sequences_preserve_empty_repeated_and_mutual_semantics(container: Callable[..., Sequence]) -> None:
  tgs = container((Tiangan.甲, Tiangan.己, Tiangan.甲))
  dzs = container((Dizhi.辰, Dizhi.辰))
  assert tiangan_utils.search(tgs, TianganRelation.合) == (frozenset({Tiangan.甲, Tiangan.己}),)
  assert tiangan_utils.discover(tgs) == tiangan_utils.discover([Tiangan.甲, Tiangan.己])
  assert tiangan_utils.discover(container(())) == {}
  assert dizhi_utils.search(dzs, DizhiRelation.刑) == (frozenset({Dizhi.辰}),)
  assert DizhiRelation.刑 not in dizhi_utils.discover(container((Dizhi.辰,)))
  assert dizhi_utils.discover(container(())) == {}
  assert tiangan_utils.discover_mutual(tgs, container(())) == {}
  assert dizhi_utils.discover_mutual(dzs, container(())) == {}
  assert dizhi_utils.discover_mutual(container((Dizhi.辰,)), container((Dizhi.辰,)))[DizhiRelation.刑] == (frozenset({Dizhi.辰}),)
