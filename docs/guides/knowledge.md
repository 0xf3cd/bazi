# 查阅知识库

不创建命盘，也可以按中文名找对象、读条文与出处、搜索文字，或编辑自己的知识文件。

```{include} ../installation.inc
```

排盘路径见 {doc}`quickstart`；不运行 Python 时可直接浏览 {doc}`../catalog/index`。
旧版调用与知识文件的迁移见 {doc}`../release-notes`。

## 按名称或 ID 找对象

直接按中文名查询；下面只读定义主题：

```{testcode} load
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
for entry in kb.query('丁', topic='定义'):
  print(entry.text)
```

```{testoutput} load
丁为阴火。
```

`kb.query('丁')` 返回丁的全部相关材料，也可传 `Tiangan.丁`、十神或五行枚举。
枚举按类别和中文名称对应对象，例如 `Wuxing.WOOD` 对应“木”，不靠英文成员名拼 ID。
字符串可以是对象 ID 或精确名称；重名时抛 `ValueError` 并列出候选，未知名称也报错。
需要查看候选时，用 `find_objects(name)`，它返回全部同名对象，无匹配返回空元组。
查询不去掉两侧空格，也不作模糊匹配；`'丁火'` 或 `'丁 '` 不会匹配“丁”。
已知条目 ID 则用 `kb.entry(claim_id)` 直接读取。

`load()` 每次读取并校验随包知识。`objects`、`sources`、`entries`
分别保存 {py:class}`~bazi.knowledge.KnowledgeObject`、{py:class}`~bazi.knowledge.KnowledgeSource`
和 {py:class}`~bazi.knowledge.KnowledgeEntry`，完整字段见各类型的 API 参考。

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
print('支持范围', source.supports)
print('来源说明', source.limitations)
```

```{testoutput} sources
《刻京台增补渊海子平大全》
李钦增补
明万历二十八年闽书林刘龙田乔山堂刊本
PDF 第 70 页左右两半叶，「十干体象」
丁火其形一燭燈〔……〕戊土城墻堤岸同〔……〕己土田園屬四維〔……〕庚金頑鈍性偏剛〔……〕辛金珠玉性虛靈〔……〕壬水汪洋併百川〔……〕癸水應非雨露麼
支持范围 丁至癸的五行称名，以及丁、戊、辛、壬的历史象。
来源说明 白文正文。丁至癸七首各取开头七字，片段间〔……〕为本仓省略标记；干名原作圈示，转录为普通字。不使这些象成为跨流派定义或性格前提。
```

这里读取第一份来源；遍历 `entry.sources` 可读到全部来源。`source.url` 是所用版本的链接，
反向用 `kb.query(source_id=source.source_id)` 找引用它的条目。
来源记录可能尚无条目引用，不能从条目反推完整来源目录。

`kb.render(entry)` 默认显示条目 ID、正文、前提、读法、署名、限度和简短出处。
`show_sources=True` 追加版本、定位、链接、引文和支持范围；必要来源说明始终显示，包括正文／夹注的区别。

## 查询与过滤

`query(subject=None, *, topic=None, source_id=None, viewpoint=None)` 可组合对象、主题、来源和读法。
多个条件取交集，结果保持语料顺序；不传条件返回全部条目。多对象条目在每个对象下都能查到，
关系方向由正文说明，对象列表不区分主次。

例如查阅文昌的两种读法：

```{testcode} shensha-knowledge
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
for entry in kb.query('文昌'):
  source = kb.sources[entry.sources[0]]
  print(entry.text)
  print(entry.viewpoint, source.work)
```

```{testoutput} shensha-knowledge
《星学大成》〈论文昌〉的夹注明定辛取戌，以戌在辛之方位解释该格。
XIN_XU 星学大成
问真《神煞大全》以“文昌贵人”为题列出辛取子的十干表，以日干或年干查四地支；对应本库文昌的辛子读法。
现代问真 问真《神煞大全》
```

`kb.query('文昌', viewpoint='XIN_XU')` 只取辛戌读法。
来源的 `limitations` 说明摘录属于正文、夹注还是原创说明；`supports` 说明它支持表值、锚点或查找位置中的哪一部分。
天乙、桃花、驿马、华盖、羊刃也有参考对象；规则与条目入口见 {doc}`rule-coverage`。

用 `kb.filter_values('topic')` 等调用列出某个维度的全部合法值，或浏览 {doc}`../catalog/filters`。
值合法但没有交集时返回空元组；未知值抛 `ValueError`，与无匹配不同。

## 字面关键词搜索

```{testcode} search
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
for entry in kb.search('火', subject='丁', topic='定义'):
  print(entry.text)
```

```{testoutput} search
丁为阴火。
```

`search` 先按 `query` 的条件过滤，再作不分大小写的字面子串匹配，无匹配返回空元组。
它搜索条文、前提、署名、主题、读法、限度和对象名称，不搜 ID 或来源全文，
不解释正则，也不自动转换繁简字。查对象 ID 请用 `query('tiangan.ding')`。

## 胎元与命宫的取法与候选

按阅读目的选 ID，用 `kb.entry(claim_id)` 或下例读文字；
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
for entry in kb.query('胎元', viewpoint='三百日候选待核'):
  print(entry.viewpoint)
  print(entry.text)
```

```{testoutput} auxiliary-knowledge
三百日候选待核
《三命通会》四库本转录有「惟有一法以當生前三百日為十月之氣乃是受胎之正」，同段末又问「然則貴人受胎定在三百日又豈可據乎」。保留三百日说为文献候选，不截句判成唯一正确规则。
```

阅读这些候选时，条目的限度和来源说明须一并读取，字段区别见下节。

## 来源与前提

条目必填 `claim_id`、`objects`、`text`；以下字段可选。表中类型指 JSON 写法；
加载后，字符串数组成为不可变元组。

| 条目字段 | JSON 类型 | 含义与显示标签 |
| --- | --- | --- |
| `topics` | 字符串数组 | 主题，可填多个；查询参数 `topic` 每次筛选其中一个主题。 |
| `premise` | 字符串 | 前提：阅读这条文字所需的条件。 |
| `viewpoint` | 字符串 | 读法：区分同一对象的不同解释或取法。 |
| `attribution` | 字符串 | 署名：这条文字归于谁；与出处引用分开填写。 |
| `sources` | 字符串数组 | 来源 ID，按此顺序读取并显示对应的来源记录。 |
| `limits` | 字符串数组 | 限度：这条文字的适用限制或尚未明确的条件，逐项显示。 |

来源必填 `source_id`、`work`；以下字段可选：

| 来源字段 | JSON 类型 | 含义与文本输出标签 |
| --- | --- | --- |
| `attribution` | 字符串 | 来源署名：来源的作者或归属。 |
| `edition` | 字符串 | 版本：所用版本。 |
| `locator` | 字符串 | 定位：页码、篇章等定位信息。 |
| `url` | 字符串 | 链接：所用版本的链接。 |
| `excerpt` | 字符串 | 引文／记录：按原文保存的摘录。 |
| `supports` | 字符串 | 支持范围：这份出处支持条目中的哪一部分。 |
| `limitations` | 字符串 | 来源说明：出处的局限及摘录的文本层次，如正文、夹注、现代编者整理。 |
| `state` | 字符串或 `null` | 来源状态：`witnessed`、`editorial`、`unverified`、`repository_attributed`；可不填。 |

省略的数组字段为空元组，省略的字符串字段为空串；`state` 省略或填 `null` 时为 `None`。

`witnessed` 表示已核原文出处，`editorial` 表示原创说明，`unverified` 表示来源尚未核实，
`repository_attributed` 表示仓内规则实现的归属。未填状态不表示已核实。
这些状态均不证明条文本身为真或适用于某张命盘，同一条目可以引用不同状态的来源。
来源说明中的“原创说明”描述摘录的文本层次，如现代编者整理，不是来源状态；
这类材料也可以有已核原文出处，标为 `witnessed`。
条目署名与来源引用分开记录；没有引用不等于内容为假，也不自动认定为作者原创。

例如读一条尚无已核出处的文字：

```{testcode} render
from bazi.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
print(kb.render(kb.entry('legacy.shishen.SH-001'), show_sources=False))
```

```{testoutput} render
条目：legacy.shishen.SH-001
代表同辈、竞争、合作。
主题：取象
读法：旧语料（未核）
署名：旧语料，出处未核
```

查到条目不表示命盘满足其前提；前提为空只表示未填写，空栏目在展示中省略。
十神与天干的旧描述中，“须结合命盘条件阅读”以及旺衰、状态、喜用等前提文字，
没有因此获得计算定义：这些条目尚未还原强弱、喜用或有效生克的完整条件。
需要判断已实现的结构条件时，使用判据入口，见 {doc}`integration`。

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
entry.setdefault('limits', []).append('个人备注：此行不是来源内容。')
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
命令行可用 `bazi knowledge 丁 --knowledge-source edited.json` 读取；完整用法见 {doc}`cli`。
备注保留个人归属，不把它写成已核原文；原来的来源状态不认证新增备注。

编辑时保留稳定 ID、原引文及来源信息；判据按 ID 关联条目，自定义库须保持同 ID 的领域含义。
当前格式是精确整数 `schema_version=4` 和 `objects`、`sources`、`entries` 三份注册表。
条目只必填 `claim_id`、`objects`、`text`；来源只必填 `source_id`、`work`，其余字段按材料填写。
例如下面是可独立加载的最小编辑源：

```json
{
  "schema_version": 4,
  "objects": [{"object_id": "my.ding", "kind": "tiangan", "name": "丁"}],
  "sources": [],
  "entries": [{"claim_id": "my.note", "objects": ["my.ding"], "text": "我的阅读笔记。"}]
}
```

加载检查字段类型、重复键／ID和断引用，不要求来源数量或证明内容正确。
对象名称可以重名，但一个对象的 ID 不能与另一个对象的名称相同；加载时会拒绝这种冲突，
以保证按 ID 查询能准确定位对象。同一对象的 ID 与名称可以相同。
断引用时 `ValueError` 会指出未知 ID 与条目；把引用改回已有记录，或补齐对应记录后再加载。
精确条件见 {doc}`../api-contract`。

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
