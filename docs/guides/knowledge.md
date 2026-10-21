# 查阅知识库

这篇教程不创建命盘。装好 `bazi` 后，你可以查对象、过滤和搜索条目、读出处，把所选条目导出再加载，也可以在内存里改一份副本。

先说一个前提：知识库记录的是**文字及其出处**，不是对命盘的判断。`witnessed`（见证）说明条目绑定了已核定的原文出处，不证明这句话为真，也不证明现实中会发生什么。

## 安装与版本

```sh
python -m pip install bazi
```

本页对应当前开发源码；已发布版本以[对应 tag](https://github.com/0xf3cd/bazi/tags) 下的说明为准。从源码试用当前接口时，在仓库根目录运行 `python -m pip install .`。
本教程全程无需出生输入；排盘路径另见 {doc}`quickstart`。

## 加载

```{testcode} load
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
print(len(kb.objects), len(kb.contexts), len(kb.sources), len(kb.entries))
```

```{testoutput} load
32 10 18 305
```

`load()` 不需要出生信息。每次调用都会重新读取并校验随包的 `knowledge_data.json`，返回不可变快照。

这四个数字对应四份注册表：

- `objects`：被讨论的对象，如天干、十神。
- `contexts`：人工选择的查阅情境，带时间范围与限度。
- `sources`：来源见证，记录书名、版本、页位、摘录和适用范围。
- `entries`：解释条目，文字、角色、主题和出处引用都在这里。

条目只引用另外三份注册表里的稳定 ID。反过来，注册表里的记录不一定有条目引用它：来源库就包含没有被任何条目用到的记录，所以不能从有引用的条目反推完整目录。

不运行 Python 也可直接浏览 {doc}`../catalog/index`。记录字段见 {py:class}`~bazi.knowledge.KnowledgeObject`、{py:class}`~bazi.knowledge.KnowledgeContext`、{py:class}`~bazi.knowledge.KnowledgeSource` 和 {py:class}`~bazi.knowledge.KnowledgeEntry`。

## 按名称或 ID 找对象

```{testcode} find
from bazi.defines import Tiangan
from bazi.knowledge import KnowledgeBase, object_id

kb = KnowledgeBase.load()
found = kb.find_objects('丁')
print([(o.object_id, o.kind) for o in found])
print(object_id(Tiangan.丁) == found[0].object_id)
print(kb.find_objects('丁火'))
print(kb.find_objects('丁 '))
try:
  kb.find_objects('  ')
except ValueError as error:
  print(type(error).__name__)
```

```{testoutput} find
[('tiangan.ding', 'tiangan')]
True
()
()
ValueError
```

`find_objects` 只做精确比较：`'丁火'` 和带空格的 `'丁 '` 都找不到对象，返回空元组；全空白名称则抛 `ValueError`。已有 `Tiangan` 或 `Shishen` 成员时，用 `object_id()` 直接得到稳定 ID。

## 查询与过滤

`query` 接受七个过滤维度：`object_id`、`context_id`、`topic`、`source_id`、`viewpoint`、`applicability`、`time_scope`。多个条件取交集，结果保持语料顺序。

```{testcode} query
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
default = kb.query(object_id='tiangan.ding')
everything = kb.query(object_id='tiangan.ding', include_reference_only=True)
print([e.claim_id for e in default])
print(len(everything))
print(len(kb.query(object_id='tiangan.ding', applicability='unconditional')))
print(len(kb.query(object_id='tiangan.ding', applicability='unconditional', include_reference_only=True)))
print('shensha.guoyin' in kb.filter_values('object_id'), kb.query(object_id='shensha.guoyin'))
print(len(kb.query(object_id='shensha.guoyin', include_reference_only=True)))
try:
  kb.query(object_id='tiangan.dingg')
except ValueError as error:
  print(type(error).__name__, error)
```

```{testoutput} query
['tiangan.ding.definition']
8
1
2
True ()
2
ValueError Unknown object_id: tiangan.dingg
```

三点区别：

- **默认与参考。** 默认只返回 `output='default'` 的条目；加 `include_reference_only=True` 才包含仅供参考的条目。丁一共 8 条，默认只有 1 条。
- **合法值不保证有结果。** `shensha.guoyin` 是合法对象，默认查询却为空，加上参考条目才有 2 条。可用的过滤值由 `filter_values(维度)` 列出。
- **未知值与无匹配不同。** 值不在 `filter_values` 里会抛 `ValueError`；值合法但没有交集，只返回空元组。

## 字面关键词搜索

```{testcode} search
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
print([e.claim_id for e in kb.search('火', object_id='tiangan.ding')])
print(len(kb.search('火', object_id='tiangan.ding', include_reference_only=True)))
print(kb.search('tiangan.ding'))
```

```{testoutput} search
['tiangan.ding.definition']
4
()
```

`search` 先按上面的规则过滤，再对条目文字、前提、署名、主题、观点、例外、限度和对象名称做不分大小写的子串匹配。它不分词，不解释正则，也不搜对象 ID、情境标签或来源全文，所以 `search('tiangan.ding')` 没有命中。对象 ID 请用 `query(object_id=...)`。

## 条目的来源

```{testcode} sources
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
entry = kb.entry('tiangan.ding.definition')
print(entry.sources)
source = kb.sources[entry.sources[0]]
print(source.work)
print(source.attribution)
print(source.edition)
print(source.locator)
print(source.lineage, source.text_layer, source.state)
print(source.excerpt)
print(source.supports)
print(source.limitations)

unverified = kb.entry('legacy.shishen.SH-001')
print(unverified.sources, unverified.source_state, unverified.output)
print([s for s in kb.sources if not kb.query(source_id=s, include_reference_only=True)])
```

```{testoutput} sources
('yuanhai_ziping_stem_symbols_p70', 'mingli_tanyuan_stem_basics')
《刻京台增补渊海子平大全》
李钦增补
明万历二十八年闽书林刘龙田乔山堂刊本
PDF 第 70 页左右两半叶，「十干体象」
yuanhai_ziping baiwen witnessed
丁火其形一燭燈戊土城墻堤岸同己土田園屬四維庚金頑鈍性偏剛辛金珠玉性虛靈壬水汪洋併百川癸水應非雨露麼
丁至癸的五行称名，以及丁、戊、辛、壬的历史象。
不使这些象成为跨流派定义或性格前提。
() unverified reference_only
['yuanhai_ziping_stem_table']
```

路径是：`kb.entry(条目 ID).sources` 给出来源 ID，再用 `kb.sources[来源 ID]` 取记录。记录里的 `work`、`attribution`、`edition`、`locator` 说明出处，`excerpt` 是摘录，`supports` 与 `limitations` 写明这段原文支持什么、不支持什么。读来源时请连 `limitations` 一起读。

反向用 `query(source_id=...)` 找引用某个来源的条目。

两种“看起来没有来源”的情形要分开：

- 条目的 `sources` 为空，且 `source_state` 为 `unverified`：出处尚未核定。这不表示没有来源，也不表示断言为假。
- 来源本身没有条目引用（上面最后一行）：它只是注册表里的记录。

`render` 把这些字段排成可读文字。`show_sources=False` 只关闭来源详情；前提与限度始终保留：

```{testcode} render
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
entry = kb.entry('legacy.shishen.SH-001')
print(kb.render(entry, show_sources=False))
```

```{testoutput} render
代表同辈、竞争、合作。【仅供参考；来源尚未核实；前提待梳理；命盘适用性未判断】
```

## 三个状态各管一件事

| 字段 | 回答什么 | 取值 |
| --- | --- | --- |
| `source_state` | 出处核定到哪一步 | `witnessed`、`editorial`、`unverified`、`repository_attributed` |
| `applicability` | 前提整理到哪一步 | `unconditional`、`described`、`unresolved` |
| `output` | 默认查询是否返回 | `default`、`reference_only` |

这些都是知识整理状态，不是某张命盘的求值结果。`applicability='described'` 只说明前提已用文字记下，术语可能还没有计算定义。

```{testcode} states
from collections import Counter

from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
counts = Counter((e.output, e.source_state) for e in kb.entries.values())
for key in sorted(counts):
  print(key, counts[key])
print(Counter(e.applicability for e in kb.entries.values()).most_common())
```

```{testoutput} states
('default', 'witnessed') 19
('reference_only', 'editorial') 22
('reference_only', 'repository_attributed') 5
('reference_only', 'unverified') 245
('reference_only', 'witnessed') 14
[('unresolved', 262), ('unconditional', 31), ('described', 12)]
```

`witnessed` 条目有 33 条，其中 14 条仍是 `reference_only`，所以 `witnessed` 不单独推出默认输出。成为 `default` 要同时满足四个条件：

1. `applicability` 为 `unconditional`；
2. `source_state` 为 `witnessed`；
3. 引用的每个来源，`state` 都与条目的 `source_state` 一致；
4. 引用的来源至少来自两个不同的 `lineage`（谱系）。

前两条在条目构造时检查，后两条在 `KnowledgeBase` 构造时检查。下面逐条触发：

```{testcode} gate
from dataclasses import replace

from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
loose = kb.entry('legacy.shishen.SH-001')
try:
  replace(loose, output='default')
except ValueError as error:
  print(type(error).__name__, error)

default = kb.entry('tiangan.ding.definition')
one_source = replace(default, sources=default.sources[:1])
print(one_source.output)
try:
  KnowledgeBase(
    tuple(kb.objects.values()), tuple(kb.contexts.values()),
    tuple(kb.sources.values()), (one_source,),
  )
except ValueError as error:
  print(type(error).__name__, error)
```

```{testoutput} gate
ValueError Ineligible default entry: legacy.shishen.SH-001
default
ValueError Default entry needs independent lineages: tiangan.ding.definition
```

第二个例子里，只留一个来源的条目通过了条目自身的检查（仍是 `default`），但放进知识库时因为只剩一个谱系被拒。另外，`source_state` 为 `unverified` 当且仅当 `sources` 为空，两者不一致也会被拒。

## 导出所选条目并重新加载

```{testcode} export
import json
import tempfile
from pathlib import Path

from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
chosen = kb.query(object_id='tiangan.ding', include_reference_only=True)
text = kb.export_json(chosen)
data = json.loads(text)
print(list(data))
print(data['schema_version'], len(data['entries']), len(data['objects']), len(data['sources']))
print(list(data['entries'][0]))
restored = KnowledgeBase.from_json(text)
print(tuple(restored.entries.values()) == chosen)
print(len(restored.entries), len(restored.objects))

with tempfile.TemporaryDirectory() as folder:
  path = Path(folder) / 'ding.json'
  path.write_text(text, encoding='utf-8')
  print(KnowledgeBase.load(path) == restored)
```

```{testoutput} export
['schema_version', 'objects', 'contexts', 'sources', 'entries']
1 8 32 18
['claim_id', 'text', 'roles', 'relations', 'topics', 'applicability', 'premise', 'contexts', 'sources', 'source_state', 'attribution', 'viewpoint', 'exceptions', 'limits', 'output', 'legacy']
True
8 32
True
```

导出的是 `schema_version`（当前为 1）加四份注册表。**条目只含你选的 8 条，但对象、情境、来源三份注册表完整保留**（32 个对象、18 个来源），所以所选条目的引用不会断。

`from_json` 与 `load(Path(...))` 走同一套校验。省略 `export_json` 的参数则导出全部条目，包括仅供参考的条目。

## 改一份本地副本

想加几行自己的备注，改导出的 JSON 副本，再加载。下面只在内存里操作，不写回随包的 `knowledge_data.json`：

```{testcode} edit
import json

from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
data = json.loads(kb.export_json(kb.query(object_id='tiangan.ding')))
entry = data['entries'][0]
entry['limits'].append('演示副本：此行为教程添加，不是来源内容。')
copy = KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))

edited = copy.entry('tiangan.ding.definition')
print(edited.claim_id, edited.text)
print(edited.limits)
print(edited.source_state, edited.output, edited.sources == kb.entry(edited.claim_id).sources)
print(kb.entry('tiangan.ding.definition').limits)
print(copy == kb)
```

```{testoutput} edit
tiangan.ding.definition 丁为阴火。
('演示副本：此行为教程添加，不是来源内容。',)
witnessed default True
()
False
```

改动只在副本里：原知识库的 `limits` 仍是空，两个库不相等。几条习惯：

- 保留稳定 ID 和原文。改了原文，就在 `limits` 里说明是你改的。
- `source_state` 仍是 `witnessed`，是因为你没动来源；它不代表你的改动已被核定。
- 要保存的话，把 JSON 文本写到你自己的文件，再用 `KnowledgeBase.load(Path(...))` 读回。

### 引用断了会怎样

把条目指向一个不存在的来源：

```{testcode} broken
import json

from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
data = json.loads(kb.export_json(kb.query(object_id='tiangan.ding')))
good = data['entries'][0]['sources']
data['entries'][0]['sources'] = ['no_such_source']
try:
  KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))
except ValueError as error:
  print(type(error).__name__, error)

data['entries'][0]['sources'] = good
print(len(KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False)).entries))
```

```{testoutput} broken
ValueError Unknown source: no_such_source (tiangan.ding.definition)
1
```

加载抛 `ValueError`，消息里带出未知的 ID 和出问题的条目。修法是让引用指回注册表里存在的 ID，要么改回，要么在 `sources` 里补上这条来源记录。对象和情境的引用同理；字段缺失、重复键、不支持的 `schema_version` 也都在加载时拒绝。

## 不建命盘浏览判据目录

`criteria()` 返回以判据 ID 为键的映射，每个值是 `CriterionInfo`：

```{testcode} criteria
from bazi.context_matching import criteria, criterion

catalog = criteria()
print(len(catalog))
for criterion_id, info in catalog.items():
  print(criterion_id, info.entry_role, info.profile_kind, len(info.claim_ids))
info = criterion('editorial.guansha_coexistence_female.v1')
print(info.claim_ids)
print(info.required_gender.value)
print(info.required_inputs, info.optional_inputs)
```

```{testoutput} criteria
8
editorial.guansha_coexistence.v1 premise context 2
editorial.guansha_coexistence_female.v1 premise context 2
tiangan.ding_weak_and_overcontrolled condition context 1
tiangan.geng_regulated_transit condition context 1
shishen.pianyin_favorable_or_balanced condition context 1
shishen.xiaoyin_duoshi condition context 1
editorial.spouse_palace_xingchong.v1 condition relationship 1
editorial.spouse_star_tougan.v1 condition relationship 1
('editorial.shishen.zhengguan.infidelity', 'editorial.shishen.qisha.infidelity')
女
('chart', 'criterion_id', 'profile') ('knowledge', 'include_reference_only')
```

这是静态目录，不判断任何命盘。`entry_role` 区分两种关联：`premise` 判关联条目的完整前提；`condition` 只判局部事实，不能据此认定条目全文的前提成立。`claim_ids` 是默认语料的约定，自定义知识库不保证有这些条目。真正对命盘求值用 `evaluate_context`，见 {doc}`integration`；字段说明见 {py:class}`~bazi.context_matching.CriterionInfo`，完整列表见 {doc}`../catalog/criteria`。

## 源码脚本

仓库根目录的 `run_interpreter.py` 是源码脚本，不随安装包发布；安装包只提供上面的 Python API。克隆仓库并装好依赖后，同样的查询与导出可以这样跑：

```sh
python run_interpreter.py knowledge --object tiangan.ding
python run_interpreter.py knowledge --list-values topic
python run_interpreter.py knowledge \
  --object tiangan.ding \
  --include-reference-only \
  --export-knowledge-json output_data/knowledge.json
```

只写 `knowledge` 会给出知识库概览和可用的查询条件；`--validate-knowledge` 校验完整知识源，`--knowledge-source` 指定你自己的 JSON，`--all` 列出全部默认可见的条目。
判据目录用 `python run_interpreter.py match` 查看，只给判据 ID 会说明它需要哪些输入。完整选项见 `python run_interpreter.py knowledge --help`。
v2.3.0 起移除不带任务名的旧平铺写法，裸调用只打印帮助。原 `--query-knowledge --object tiangan.ding`
改为 `knowledge --object tiangan.ding`；不带筛选的 `--query-knowledge` 改为 `knowledge --all`。
命盘调用 `--seed 236` 改为 `chart --seed 236`，`--match-context 判据ID …` 改为 `match 判据ID …`，
上面的新写法都接在 `python run_interpreter.py` 后。
原来同时展示命盘并导出知识 TXT 的调用，拆成 `chart …` 和 `knowledge --export-knowledge-base …` 两条独立命令，
没有跨命令的冲突预检或整体回滚；每条命令仍检查自己的输出冲突及知识源覆盖。

字段与方法的完整说明见 {py:class}`~bazi.knowledge.KnowledgeBase` 和 {doc}`../api/index`，本文只讲上手路径。
