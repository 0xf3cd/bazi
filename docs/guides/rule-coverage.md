# 规则、知识与出处的覆盖

能计算一条规则、能查到解释文字、能追溯该条规则的出处，是三件不同的事。本页对账现有实现与知识目录，介绍常用神煞的参考条目，并用国印两读演示规则到条目、再到来源的查询。

## 读表口径

- **实现**以规则表、定义枚举、计算入口与配置字段为准，不能从已有知识对象反推全部计算能力。
- **知识关联**指现有对象、条目和来源 ID。文字提到某个词，不等于已经有该规则的专门对象或结构化关联。
- **来源入口**留在规则旁的注释和定义 docstring；独有的读法及来源限度沿条目 ID 查阅，简单的书名篇名或链接可直接留在源码。
- 来源的 `repository_attributed` 是本仓署名，`witnessed` 是已核原文出处，二者不互换。状态与条目前提的含义见 {doc}`knowledge`。
- 表中写“尚无对象”或“没有关联”，只表示当前没有专门的知识关联，不表示该计算没有依据，也不是新增知识对象的计划。

## 规则与配置覆盖

下表按规则族组织，覆盖 {py:class}`~bazi.rules.BaziRules`、{py:class}`~bazi.rules.TianganRules`、{py:class}`~bazi.rules.DizhiRules`、{py:class}`~bazi.rules.ShenshaRules` 的公共带注解属性，以及 {py:class}`~bazi.school.BaziSchool`、{py:class}`~bazi.school.BaziConfig` 的字段。派生表、共享定义和独立规则不按属性数混算成一个“知识覆盖率”。

### 基础表与天干关系

| 规则族 | 实现与配置 | 知识、出处与缺口 |
| --- | --- | --- |
| 年上起月、日上起时 | {py:attr}`~bazi.rules.BaziRules.YEAR_TO_MONTH_TABLE`、{py:attr}`~bazi.rules.BaziRules.DAY_TO_HOUR_TABLE`；推算入口在 {py:mod}`~bazi.utils.bazi_utils` | 表旁说明起干与推算含义；当前知识对象目录没有这两类规则的专门对象。 |
| 干支阴阳五行 | {py:attr}`~bazi.rules.BaziRules.TIANGAN_TRAITS`、{py:attr}`~bazi.rules.BaziRules.DIZHI_TRAITS` | `tiangan.*.definition` 已记录十干定义及出处，覆盖限于十干；地支尚无对象与来源关联。 |
| 月令五行状态 | {py:attr}`~bazi.rules.BaziRules.MONTH_WUXING`、{py:attr}`~bazi.bazi_chart.BaziChart.wuxing_states`；{py:attr}`~bazi.school.BaziSchool.tuwang_def` | 五状态与分段取法的出处见 {py:class}`~bazi.school.TuwangDef` 及表旁说明；默认整季月采用本库的简化取法。知识目录尚无对应的对象或 `KnowledgeSource`，用法见 {doc}`configuration`。 |
| 藏干及比例 | {py:attr}`~bazi.rules.BaziRules.HIDDEN_TIANGANS` | 源码列成员与百分比，表旁未列各比例的出处；尚无专门知识对象。十神释义不能替这些比例作证。 |
| 纳音 | {py:attr}`~bazi.rules.BaziRules.NAYIN` | 源码将六十甲子映射为纳音；尚无纳音对象及条目关联。 |
| 十二长生 | {py:attr}`~bazi.rules.BaziRules.TIANGAN_ZHANGSHENG`；查询与逆查在 {py:mod}`~bazi.utils.bazi_utils` | 长生起点与阳顺阴逆的计算在源码；尚无十二长生对象及条目关联。 |
| 十干禄位 | {py:attr}`~bazi.rules.BaziRules.TIANGAN_LU` | 神煞层的 `LUSHEN` 共用此表，其源码注释列出处；知识库尚无禄位专门对象。 |
| 天干合、冲 | {py:attr}`~bazi.rules.TianganRules.TIANGAN_HE`、{py:attr}`~bazi.rules.TianganRules.TIANGAN_CHONG` | 表旁说明组合与方向；知识库已有十干对象，但这两张关系表尚未关联来源记录。 |
| 天干生、克 | {py:attr}`~bazi.rules.TianganRules.TIANGAN_SHENG`、{py:attr}`~bazi.rules.TianganRules.TIANGAN_KE` | 由五行关系派生；知识库的本仓署名示例为 `wuxing.mu_sheng_huo`、`wuxing.jin_ke_mu`，其余生克组合尚无完整来源目录。 |

### 地支关系

直接查法与批量查法见 {py:mod}`~bazi.utils.dizhi_utils`。{py:class}`~bazi.rules.DizhiRelationDefinitions` 承载暗合、刑与拱局定义，{py:meth}`~bazi.school.BaziSchool.relation_definitions` 从流派配置取得同一组定义。地支关系尚无完整的来源目录；地支破的同名区别已有知识条目，其余出处见下表。

| 规则族 | 实现与配置 | 知识、出处与缺口 |
| --- | --- | --- |
| 三会、六合、三合、半合 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_SANHUI`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_LIUHE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_SANHE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_BANHE` | 表旁给出组合与结果；结构命中不自动证明合化成立或吉凶解释。 |
| 暗合、通合、通禄合 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_ANHE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_TONGHE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_TONGLUHE`；{py:attr}`~bazi.school.BaziSchool.anhe_def` | {py:class}`~bazi.rules.DizhiRules.AnheDef` 列三读；`NORMAL` 暗合与通禄合给出相同组合，不是两份独立证据。 |
| 拱合、拱会与成立条件 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_GONGHE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_GONGHUI`、{py:attr}`~bazi.rules.DizhiRules.GONG_RELATIONS`、{py:attr}`~bazi.rules.DizhiRules.GONG_GONGHE_SCOPE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_GONG_LU_TIANGAN`；{py:attr}`~bazi.school.BaziSchool.gong_def` | {py:class}`~bazi.rules.DizhiRules.GongheDef` 管结构，{py:class}`~bazi.rules.DizhiRules.GongDef` 保存同干、透化神、见禄字的完整来源档案。后者列现代来源与适用范围，不任意拼接成新读法。 |
| 刑 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_XING`；{py:attr}`~bazi.school.BaziSchool.xing_def` | {py:class}`~bazi.rules.DizhiRules.XingDef` 区分严格／宽松；按序查法可见方向，批量入口按多重集比较，不能混作同一方向语义。 |
| 冲、破、害 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_CHONG`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_PO`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_HAI` | 表旁给出无方向组合；`concept.dizhi_po.readings` 区分六对地支破与同名神煞，不为全部关系表作证。 |
| 地支生、克 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_SHENG`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_KE` | 只从地支五行派生，不考虑阴阳；五行的两个知识示例不覆盖地支间全部应用。 |

### 神煞

低层查法见 {py:mod}`~bazi.utils.shensha_utils`，规则表见 {py:class}`~bazi.rules.ShenshaRules`。
锚点选项见 {doc}`configuration`，原局与流运的查法见 {doc}`relations-transits`。
表值、锚点和查找位置各自的出处，沿下表的知识条目读取。

先用 `kb = 知识库.load()` 加载知识库，再用 `kb.query('红艳')` 按中文名称读取相关说明，
或用 `kb.entry(条目ID)` 精确读取。
迁自源码的说明引用 `repository.rule_readings`，原有已核来源各自保留。
问真与高人的计数及未知关系见 `concept.shensha_sources.readings`；
袁氏日锚档案见 `concept.mingli_tanyuan.readings`。查询用法见 {doc}`knowledge`。

| 规则族 | 实现与配置 | 知识、出处与缺口 |
| --- | --- | --- |
| 桃花、红艳 | {py:attr}`~bazi.rules.ShenshaRules.TAOHUA`、{py:attr}`~bazi.rules.ShenshaRules.HONGYAN`；{py:attr}`~bazi.school.BaziSchool.hongyan_anchor` | `shensha.taohua.readings` 分开表值、夹注条件与现代查法；`shensha.hongyan.readings` 分列三份表的差异及锚点依据。 |
| 红鸾、天喜 | {py:attr}`~bazi.rules.ShenshaRules.HONGLUAN`、{py:attr}`~bazi.rules.ShenshaRules.TIANXI` | `shensha.hongluan_tianxi.readings` 区分宫限表值与现代四柱查法。 |
| 驿马、华盖 | {py:attr}`~bazi.rules.ShenshaRules.YIMA`、{py:attr}`~bazi.rules.ShenshaRules.HUAGAI`；{py:attr}`~bazi.school.BaziSchool.yima_anchor`、{py:attr}`~bazi.school.BaziSchool.huagai_anchor` | 各自的 `.table`、`.lookup` 条目记录古籍表值与现代查法；`shensha.huagai.readings` 保留袁氏转引的定位，日锚另见上述档案。 |
| 将星、灾煞 | {py:attr}`~bazi.rules.ShenshaRules.JIANGXING`、{py:attr}`~bazi.rules.ShenshaRules.ZAISHA`；{py:attr}`~bazi.school.BaziSchool.jiangxing_anchor`、{py:attr}`~bazi.school.BaziSchool.zaisha_anchor` | `shensha.jiangxing.readings`、`shensha.zaisha.readings` 分别记录表值与查法。 |
| 劫煞、亡神 | {py:attr}`~bazi.rules.ShenshaRules.JIESHA`、{py:attr}`~bazi.rules.ShenshaRules.WANGSHEN`；{py:attr}`~bazi.school.BaziSchool.jiesha_anchor`、{py:attr}`~bazi.school.BaziSchool.wangshen_anchor` | `shensha.jiesha_wangshen.readings` 记录绝位／临官位与现代双锚，日锚另沿袁氏档案读取。 |
| 孤辰、寡宿 | {py:attr}`~bazi.rules.ShenshaRules.GUCHEN`、{py:attr}`~bazi.rules.ShenshaRules.GUASU` | `shensha.guchen_guasu.readings` 记录规则、锚点与解释层豁免的区别。 |
| 禄神、金舆 | {py:attr}`~bazi.rules.ShenshaRules.LUSHEN`、{py:attr}`~bazi.rules.ShenshaRules.JINYU`；{py:attr}`~bazi.school.BaziSchool.jinyu_anchor` | 禄神共用基础禄位表，出处留在表旁；金舆的表值与锚点见 `shensha.jinyu.readings`。 |
| 魁罡、天赦 | {py:attr}`~bazi.rules.ShenshaRules.KUIGANG`、{py:attr}`~bazi.rules.ShenshaRules.TIANSHE` | 表旁列规则与出处，低层查法分别接收日柱、月令与日柱；原局分析器在 `_REGISTRY` 之外单独输出这两项整柱结果。 |
| 羊刃、飞刃 | {py:attr}`~bazi.rules.ShenshaRules.YANGREN`、{py:attr}`~bazi.rules.ShenshaRules.FEIREN`；{py:attr}`~bazi.school.BaziSchool.yangren_def`、{py:attr}`~bazi.school.BaziSchool.feiren_def` | {py:class}`~bazi.rules.ShenshaRules.YangrenDef` 定义三读；`shensha.yangren_feiren.readings` 记录出处及两星的对应关系。 |
| 天乙贵人 | {py:attr}`~bazi.rules.ShenshaRules.TIANYI`；{py:attr}`~bazi.school.BaziSchool.tianyi_def`、{py:attr}`~bazi.school.BaziSchool.tianyi_anchor` | `shensha.tianyi.readings` 分开四表、使用时段与锚点的来源；已有短条目可按具体读法查询。 |
| 文昌 | {py:attr}`~bazi.rules.ShenshaRules.WENCHANG`；{py:attr}`~bazi.school.BaziSchool.wenchang_def`、{py:attr}`~bazi.school.BaziSchool.wenchang_anchor` | `shensha.wenchang.readings` 分列辛子／辛戌，保留表值、锚点与查找位置各自的依据。 |
| 文昌贵 | {py:attr}`~bazi.rules.ShenshaRules.WENCHANGGUI` | `shensha.wenchanggui.readings` 记录全表与年干锚，和文昌分列。 |
| 太极贵人 | {py:attr}`~bazi.rules.ShenshaRules.TAIJI`；{py:attr}`~bazi.school.BaziSchool.taiji_def`、{py:attr}`~bazi.school.BaziSchool.taiji_anchor` | `shensha.taiji.readings` 保存壬癸两读、文字差异、戊己格矛盾及锚点依据。 |
| 国印贵人 | {py:attr}`~bazi.rules.ShenshaRules.GUOYIN`；{py:attr}`~bazi.school.BaziSchool.guoyin_def`、{py:attr}`~bazi.school.BaziSchool.guoyin_anchor` | `shensha.guoyin.readings` 分开两表、锚点、查找位置与传抄限度；两条取法短条目见下方示例。 |
| 六甲旬空 | {py:attr}`~bazi.rules.ShenshaRules.KONGWANG`；{py:attr}`~bazi.school.BaziSchool.kongwang_anchor` | `shensha.kongwang.xunkong` 记基础二支，`.lookup` 记汇编转引与年日例，`.repository` 记本库默认和范围。来源分列固定 revision 转录、下游白文、注释层与仓内政策；汇编所引原书尚未亲见。查法见 {doc}`relations-transits`，不含单支筛选、截路、四大或解释层。 |

### 表外计算、配置与评估边界

{py:attr}`~bazi.school.BaziConfig.school` 选择整个流派档案。其余配置和纯计算规则不能从四个规则容器的属性清单中省略。

| 规则族／边界 | 实现与配置 | 知识、出处与缺口 |
| --- | --- | --- |
| 五行、干支循环 | {py:class}`~bazi.defines.Wuxing`、{py:class}`~bazi.defines.Ganzhi`；{py:func}`~bazi.utils.bazi_utils.ganzhi_of_year`、{py:func}`~bazi.utils.bazi_utils.ganzhi_of_day` | 五行两条本仓署名示例已存在；年／日干支计算有源码定义与基准日期，但尚无相应规则到知识来源的关联。 |
| 十神计算 | {py:func}`~bazi.utils.bazi_utils.shishen` | 已有 `shishen.*` 对象与定义条目，如 `shishen.bijian.definition`；定义条目不为地支取主气、藏干比例或全部解释作证，也不能由此假定十个对象都有定义条目。 |
| 通根与透干 | {py:func}`~bazi.analyzer.facts.tonggen`、{py:func}`~bazi.analyzer.facts.tougan` | `concept.tonggen.readings` 收同五行通根例；`concept.tougan.readings` 收徐注墓库透干例。用法见 {doc}`relations-transits`。 |
| 四柱节界与换日 | {py:class}`~bazi.bazi.Bazi`；{py:attr}`~bazi.school.BaziConfig.precision`、{py:attr}`~bazi.school.BaziSchool.day_rollover` | {py:class}`~bazi.school.BaziPrecision`、{py:class}`~bazi.school.DayRollover` 与 {doc}`configuration` 说明边界。知识目录不是历法精度或换日出处目录。 |
| 胎元与命宫附加查询 | {py:attr}`~bazi.bazi_chart.BaziChart.taiyuan`、{py:attr}`~bazi.bazi_chart.BaziChart.minggong`；纯函数在 {py:mod}`~bazi.utils.bazi_utils` | `concept.taiyuan`、`concept.minggong` 区分月柱顺移、掌诀、中气按语、本库执行政策与待核候选。三百日胎元及其他命宫月界未编码；两项只作附加查询，不扩展四柱、配置或其他分析，计算不认证解释。用法见 {doc}`integration`。 |
| 历法、民用钟与真太阳钟 | {py:mod}`~bazi.calendar.utils`、{py:mod}`~bazi.calendar.solar_time` 与地点输入 | 数据来源与支持范围见 {doc}`calendar`，比较精度及钟的边界见 {doc}`configuration`。本页不评估历书和天文数据本身是否准确。 |
| 配偶星与配偶宫 | {py:attr}`~bazi.school.BaziSchool.peiou_xing_def`；{py:class}`~bazi.school.PeiouXingDef` 与 {py:class}`~bazi.bazi_chart.BaziChart` | 已有 `concept.peiou_xing`、`concept.peiou_gong` 及带原文来源的条目；历史读法、软件默认与适用条件仍须分别读取。 |
| 交运、小运、大运与流年 | {py:class}`~bazi.bazi_chart.BaziChart`；{py:attr}`~bazi.school.BaziConfig.dayun_year_rule` 与 {py:class}`~bazi.school.DayunYearRule` | 顺逆、间隔折算、物理时刻线与年份标签在源码说明中；当前没有相应专门知识对象。标签规则不能代替物理边界规则。 |
| 流运查询与关系组合 | {py:mod}`~bazi.transits`、{py:mod}`~bazi.utils.tiangan_utils`、{py:mod}`~bazi.utils.dizhi_utils`、{py:mod}`~bazi.analyzer.relationship` | 查询坐标、候选组合及原局／流运消费者各有语义；复用一张规则表不证明每种使用范围都有同一出处。 |
| 解释前提匹配 | {py:mod}`~bazi.context_matching` 与 {doc}`../catalog/criteria` | 已有判据目录与知识引用，前提是否满足须另行求值；目录本身不证明前提成立，也不覆盖全库计算规则的来源。 |

(guoyin-knowledge)=
## 国印关联示例

计算用 `GuoyinDef` 选择规则表；知识用对象和读法查询，再沿 `entry.sources` 查来源：

```{testcode} guoyin-lookup
from bazi.knowledge import KnowledgeBase
from bazi.defines import Tiangan
from bazi.rules import ShenshaRules

kb = KnowledgeBase.load()
entry, = kb.query('国印贵人', viewpoint='MODERN')
definition = ShenshaRules.GuoyinDef.MODERN
print('取法', definition.name, '甲见' + str(ShenshaRules.GUOYIN[definition][Tiangan.甲]))
print(entry.text)
for limit in entry.limits:
  print('限度：' + limit)
source = kb.sources[entry.sources[0]]
print('支持范围', source.supports)
print('来源说明', source.limitations)
```

```{testoutput} guoyin-lookup
取法 MODERN 甲见戌
国印的 MODERN 表按禄前第九位（含禄，偏移 +8）取值。
限度：表值与四柱查法的支持来源分开；古籍的守照身命表述不等于查四柱地支。
限度：本条转述仓内来源边界，未新增已核古籍见证。
支持范围 现有的两种表读法，以及另行说明的锚点／目标边界。
来源说明 原创说明。概述本仓署名，未增加已核实的古籍见证。文本源流仍未厘清。
```

查询 `viewpoint='WUXING_JINGJI'` 可读另一条知识，计算表则用 `GuoyinDef.WUXING_JINGJI`。
已有流派配置时，计算继续使用 `school.guoyin_def`。知识读法文字与枚举之间没有自动绑定。

这段代码只查表与知识，不创建命盘，也不执行“以哪柱查哪些位置”的命盘求值。三层支持要分别读：

| 层 | 当前事实从哪里取 | 来源边界 |
| --- | --- | --- |
| 表值 | `ShenshaRules.GUOYIN`、`GuoyinDef` | `shensha.guoyin.readings` 分列原文、今人注释、抄本与现代读法。 |
| 锚点 | `BaziSchool.guoyin_anchor`；支持年锚、年日双锚 | 同条目另列年干锚的今人注释依据。 |
| 查找位置 | 原局、流运分析入口 | 同条目区分果老文献的身命宫与现代四柱地支查法。 |

`repository_guoyin_variants` 概述的是本仓说明，`supports` 及 `limitations` 都应保留阅读。该来源引用固定的仓内快照；当前表与条目对账成功，不会把历史快照变成新增的古籍见证。
完整说明用 `kb.entry('shensha.guoyin.readings')` 读取，它引用另一个固定快照
`repository.rule_readings`，保留各载体、文本层次与尚未厘清的来源关系。

维护关联或补出处时，按 {doc}`../contributing` 分别说明规则、锚点、查找位置和来源的支持范围。
