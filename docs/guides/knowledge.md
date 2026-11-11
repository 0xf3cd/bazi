# 查阅知识库

不创建命盘，也可以按中文名找对象、读条文与出处、搜索文字，或编辑自己的知识文件。
知识库记录文字及出处；`witnessed` 说明原文出处已经核定，不证明条文本身为真或适用于某张命盘。

```{include} ../installation.inc
```

排盘路径见 {doc}`quickstart`；不运行 Python 时可直接浏览 {doc}`../catalog/index`。

## 按名称或 ID 找对象

先按中文名找到“丁”，再查询并读出条文：

```{testcode} load
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
for obj in kb.find_objects('丁'):
  print(obj.name, obj.object_id)
  for entry in kb.query(object_id=obj.object_id):
    print(kb.render(entry, show_sources=False))
```

```{testoutput} load
丁 tiangan.ding
丁为阴火。
```

`find_objects` 精确匹配名称，重名会全部返回，无匹配则返回空元组。它不去掉名称两侧空格，也不作模糊搜索；
`'丁火'` 或 `'丁 '` 不会匹配“丁”。已有 `Tiangan.丁` 或十神枚举时，可用 `bazi.knowledge.object_id(成员)` 得到稳定 ID。
已知条目 ID 则用 `kb.entry(claim_id)` 直接读取。

`load()` 每次读取并校验随包知识，返回不可变对象。`objects`、`contexts`、`sources`、`entries`
分别保存对象、人工查阅情境、来源记录和条目；完整字段见 {py:class}`~bazi.knowledge.KnowledgeBase`。

(knowledge-sources)=
## 条目的来源

条目的 `sources` 给出来源 ID，用 `kb.sources[来源 ID]` 读取作品、版本、位置、摘录、支持范围和限度：

```{testcode} sources
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
entry = kb.entry('tiangan.ding.definition')
source = kb.sources[entry.sources[0]]
print(source.work)
print(source.attribution)
print(source.edition)
print(source.locator)
print(source.excerpt)
print('支持', source.supports)
print('限度', source.limitations)
```

```{testoutput} sources
《刻京台增补渊海子平大全》
李钦增补
明万历二十八年闽书林刘龙田乔山堂刊本
PDF 第 70 页左右两半叶，「十干体象」
丁火其形一燭燈〔……〕戊土城墻堤岸同〔……〕己土田園屬四維〔……〕庚金頑鈍性偏剛〔……〕辛金珠玉性虛靈〔……〕壬水汪洋併百川〔……〕癸水應非雨露麼
支持 丁至癸的五行称名，以及丁、戊、辛、壬的历史象。
限度 丁至癸七首各取开头七字，片段间〔……〕为本仓省略标记；干名原作圈示，转录为普通字。不使这些象成为跨流派定义或性格前提。
```

这里读取第一份来源；遍历 `entry.sources` 可读到全部来源。`source.url` 是所用版本的链接，
反向用 `kb.query(source_id=source.source_id, include_reference_only=True)` 找引用它的条目。
来源记录可能尚无条目引用，不能从条目反推完整来源目录。

`kb.render(entry)` 默认连同来源、前提和限度一起显示；`show_sources=False` 只关闭来源详情，不隐藏前提或限度。
条目里的 `source_state` 显示为“来源状态”，来源自身的 `state` 显示为“见证状态”。

## 查询与过滤

`query` 可组合七种条件：`object_id`、`context_id`、`topic`、`source_id`、`viewpoint`、`applicability`、`time_scope`。
多个条件取交集，结果保持语料顺序。默认只返回 `show_by_default=True` 的条目；加 `include_reference_only=True` 才包含参考条目。

例如文昌的条目均仅供参考，须显式包含，再读取各读法的文字：

```{testcode} shensha-knowledge
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
for entry in kb.query(object_id='shensha.wenchang', include_reference_only=True):
  source = kb.sources[entry.sources[0]]
  print(entry.text)
  print(entry.viewpoint, source.work, source.text_layer)
```

```{testoutput} shensha-knowledge
《星学大成》〈论文昌〉的夹注明定辛取戌，以戌在辛之方位解释该格。
XIN_XU 星学大成 zhushi
问真《神煞大全》以“文昌贵人”为题列出辛取子的十干表，以日干或年干查四地支；对应本库文昌的辛子读法。
现代问真 问真《神煞大全》 editorial
```

`viewpoint` 可用于进一步过滤。`text_layer` 中 `zhushi` 表示夹注，`editorial` 表示现代编者整理；
各来源的 `supports`、`limitations` 分别说明它支持表值、锚点或查找位置中的哪一部分。
天乙、桃花、驿马、华盖、羊刃也有参考对象；规则与条目入口见 {doc}`rule-coverage`。

用 `kb.filter_values('topic')` 等调用列出某个维度的全部合法值，或浏览 {doc}`../catalog/filters`。
值合法但没有交集时返回空元组；未知值抛 `ValueError`，与无匹配不同。查阅 `context_id` 是人工过滤，不执行命盘前提判别。

## 字面关键词搜索

```{testcode} search
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
for entry in kb.search('火', object_id='tiangan.ding'):
  print(kb.render(entry, show_sources=False))
```

```{testoutput} search
丁为阴火。
```

`search` 先按 `query` 的条件过滤，再作不分大小写的字面子串匹配；也可显式包含参考条目。
它搜索条文、前提、署名、主题、观点、例外、限度和对象名称，不搜 ID、情境标签或来源全文，
不解释正则，也不自动转换繁简字。查对象 ID 请用 `query(object_id=...)`。

## 胎元与命宫的取法与候选

这两个对象的全部条目都仅供参考。按阅读目的选 ID，用 `kb.entry(claim_id)` 或下例读文字；
计算入口见 {doc}`integration`。

| 想了解什么 | 条目 ID |
| --- | --- |
| 本库胎元的月柱顺移算法 | `concept.taiyuan.repository` |
| 本库命宫的中气进月、精度与地点钟政策 | `concept.minggong.repository` |
| 胎元例解、命宫掌诀与中气按语 | `concept.taiyuan.month_shift`、`concept.minggong.palm`、`concept.minggong.zhongqi` |
| 尚无计算入口的其他读法 | `concept.taiyuan.three_hundred_days`、`concept.minggong.month_boundary_candidates` |

```{testcode} auxiliary-knowledge
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
for entry in kb.query(object_id='concept.taiyuan', applicability='unresolved', include_reference_only=True):
  print(entry.viewpoint)
  print(entry.text)
```

```{testoutput} auxiliary-knowledge
三百日候选待核
《三命通会》四库本转录有「惟有一法以當生前三百日為十月之氣乃是受胎之正」，同段末又问「然則貴人受胎定在三百日又豈可據乎」。保留三百日说为文献候选，不截句判成唯一正确规则。
```

各条目的 `limits` 和来源的 `supports`、`limitations` 分别保存原文支持范围及版本、校读差异，读出处时一并读取。

## 来源、前提与默认展示

| 字段 | 回答什么 | 取值 |
| --- | --- | --- |
| `source_state` | 出处核定到哪一步 | `witnessed`、`editorial`、`unverified`、`repository_attributed` |
| `applicability` | 前提整理到哪一步 | `unconditional`、`described`、`unresolved` |
| `show_by_default` | 默认查询是否返回 | `True`、`False` |

`witnessed` 是已核原文出处，`editorial` 是原作说明，`repository_attributed` 是仓内规则实现的归属，
`unverified` 是出处尚未核定，此时 `sources` 为空。
`described` 只说明前提已经用文字写下，术语仍可能没有计算定义。

例如旧条文的展示会保留来源和适用性提醒：

```{testcode} render
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
print(kb.render(kb.entry('legacy.shishen.SH-001'), show_sources=False))
```

```{testoutput} render
代表同辈、竞争、合作。【仅供参考；来源尚未核实；前提待梳理；命盘适用性未判断】
```

默认展示要求 `applicability='unconditional'`、`source_state='witnessed'`，
每份来源状态与条目一致，且来源至少属于两个不同 `lineage`。两个转载站点不自动构成独立谱系。
已核来源的条目仍可不默认展示；加载器会校验这些条件，来源状态与命盘前提须分别理解。

(knowledge-edit)=
## 保存并编辑自己的知识文件

从随包知识源复制一份，给副本添加自己的备注，再加载。下面会在当前目录创建或覆盖 `edited.json`；
已有同名文件时请先另存。不会写回安装包里的 `knowledge_data.json`。

```{testsetup} edit
import os
import subprocess
import sys
import tempfile

_edit_cwd = os.getcwd()
_edit_directory = tempfile.TemporaryDirectory()
os.chdir(_edit_directory.name)
```

```{testcode} edit
import json
from pathlib import Path

from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase

data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
entry = next(value for value in data['entries'] if value['claim_id'] == 'tiangan.ding.definition')
entry['limits'].append('个人备注：此行不是来源内容。')
path = Path('edited.json')
path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

copy = KnowledgeBase.load(path)
edited = copy.entry('tiangan.ding.definition')
print('已保存', path)
print(edited.text)
print(edited.limits[-1])
```

```{testoutput} edit
已保存 edited.json
丁为阴火。
个人备注：此行不是来源内容。
```

```{testcleanup} edit
try:
  assert path.is_file()
  _reloaded = subprocess.run(
    [sys.executable, '-c', "from pathlib import Path; from bazi.knowledge import KnowledgeBase; print(KnowledgeBase.load(Path('edited.json')).entry('tiangan.ding.definition').limits[-1])"],
    env=os.environ | {'PYTHONPATH': os.environ['BAZI_DOC_ROOT']},
    capture_output=True, text=True, encoding='utf-8', timeout=30, check=True,
  )
  assert _reloaded.stdout.strip() == '个人备注：此行不是来源内容。'
finally:
  os.chdir(_edit_cwd)
  _edit_directory.cleanup()
```

文件会留在运行代码的目录，以后可用 `KnowledgeBase.load(Path('edited.json'))` 重新加载。
命令行可用 `bazi knowledge --knowledge-source edited.json --object tiangan.ding` 读取；完整用法见 {doc}`cli`。
备注保留个人归属，不把它写成已核原文；原来的来源状态不认证新增备注。

编辑时保留稳定 ID、原引文及来源信息；判据按 ID 关联条目，自定义库须保持同 ID 的领域含义。
当前格式是精确整数 `schema_version=3` 和四份注册表，
条目以 JSON boolean `show_by_default` 控制默认展示，不接受旧 `output` 键、其他 schema 或自动迁移。
已有编辑源的升级见 {doc}`../release-notes`。

加载会检查字段、重复键、状态和引用。断引用时 `ValueError` 会指出未知 ID 与条目；
把引用改回已有记录，或在相应注册表中补齐可核的记录后再加载。孤立代理项会被拒绝，不修复原文；
中文、非 BMP 字符和合法 JSON 转义仍可使用。精确条件见 {doc}`../api-contract`。

## 不建命盘浏览判据目录

`criteria()` 和 `criterion(id)` 只读静态目录，不创建命盘、不加载知识，也不执行判别。
例如读取一个判据的定义和可用范围：

```{testcode} criteria
from bazi.context_matching import criterion

info = criterion('editorial.guansha_coexistence.v1')
print(info.definition)
print('支持范围', ', '.join(info.scopes))
print('关联语义', info.entry_role)
```

```{testoutput} criteria
选定范围内正官与七杀各至少出现一次。
支持范围 natal, natal_and_liunian
关联语义 premise
```

`entry_role='premise'` 检查关联条目的完整前提，`'condition'` 只检查局部事实。
全部判据及所需输入见 {doc}`../catalog/criteria`；对命盘求值并读取结果见 {doc}`integration`。
