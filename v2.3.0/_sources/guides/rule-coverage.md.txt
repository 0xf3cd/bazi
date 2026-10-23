# 规则、知识与出处的覆盖

能计算一条规则、能查到解释文字、能追溯该条规则的出处，是三件不同的事。本页对账现有实现与知识目录，并用国印两读说明如何把它们连起来；不增加规则、查询接口或来源见证。

## 读表口径

- **实现**以规则表、定义枚举、计算入口与配置字段为准，不能从已有知识对象反推全部计算能力。
- **知识关联**指现有对象、条目和来源 ID。文字提到某个词，不等于已经有该规则的专门对象或结构化关联。
- **源码出处**包括规则旁的注释和定义 docstring。本页只记录这些说明的位置与支持边界，没有重新核验其外部古籍或天文数据。
- `repository_attributed` 是本仓署名，`witnessed` 是已核原文出处，二者不互换；`reference_only` 另管默认输出资格。状态的完整含义见 {doc}`knowledge`。

## 规则与配置覆盖

下表按规则族组织，覆盖 {py:class}`~bazi.rules.BaziRules`、{py:class}`~bazi.rules.TianganRules`、{py:class}`~bazi.rules.DizhiRules`、{py:class}`~bazi.rules.ShenshaRules` 的公共带注解属性，以及 {py:class}`~bazi.school.BaziSchool`、{py:class}`~bazi.school.BaziConfig` 的字段。派生表、共享定义和独立规则不按属性数混算成一个“知识覆盖率”。

### 基础表与天干关系

| 规则族 | 实现与配置 | 知识、出处与缺口 |
| --- | --- | --- |
| 年上起月、日上起时 | {py:attr}`~bazi.rules.BaziRules.YEAR_TO_MONTH_TABLE`、{py:attr}`~bazi.rules.BaziRules.DAY_TO_HOUR_TABLE`；推算入口在 {py:mod}`~bazi.utils.bazi_utils` | 表旁说明起干与推算含义；当前知识对象目录没有这两类规则的专门对象。 |
| 干支阴阳五行 | {py:attr}`~bazi.rules.BaziRules.TIANGAN_TRAITS`、{py:attr}`~bazi.rules.BaziRules.DIZHI_TRAITS` | `tiangan.*.definition` 已记录十干定义及出处；没有地支对象，不能把十干定义的覆盖扩大到地支表。 |
| 藏干及比例 | {py:attr}`~bazi.rules.BaziRules.HIDDEN_TIANGANS` | 源码列成员与百分比，表旁未列各比例的出处；尚无专门知识对象。十神释义不能替这些比例作证。 |
| 纳音 | {py:attr}`~bazi.rules.BaziRules.NAYIN` | 源码将六十甲子映射为纳音；尚无纳音对象及条目关联。 |
| 十二长生 | {py:attr}`~bazi.rules.BaziRules.TIANGAN_ZHANGSHENG`；查询与逆查在 {py:mod}`~bazi.utils.bazi_utils` | 长生起点与阳顺阴逆的计算在源码；尚无十二长生对象及条目关联。 |
| 十干禄位 | {py:attr}`~bazi.rules.BaziRules.TIANGAN_LU` | 神煞层的 `LUSHEN` 共用此表，其源码注释列出处；知识库尚无禄位专门对象。 |
| 天干合、冲 | {py:attr}`~bazi.rules.TianganRules.TIANGAN_HE`、{py:attr}`~bazi.rules.TianganRules.TIANGAN_CHONG` | 表旁说明组合与方向；十干对象存在，不代表这两张关系表已关联到来源记录。 |
| 天干生、克 | {py:attr}`~bazi.rules.TianganRules.TIANGAN_SHENG`、{py:attr}`~bazi.rules.TianganRules.TIANGAN_KE` | 由五行关系派生；已有 `wuxing.mu_sheng_huo`、`wuxing.jin_ke_mu` 两条本仓署名示例，不是全体生克组合的来源目录。 |

### 地支关系

直接查法与批量查法见 {py:mod}`~bazi.utils.dizhi_utils`。{py:class}`~bazi.rules.DizhiRelationDefinitions` 承载暗合、刑与拱局定义，{py:meth}`~bazi.school.BaziSchool.relation_definitions` 从流派配置取得同一组定义。当前知识对象目录没有地支关系对象；下列出处仍在源码说明中，没有统一的规则到来源 ID 索引。

| 规则族 | 实现与配置 | 知识、出处与缺口 |
| --- | --- | --- |
| 三会、六合、三合、半合 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_SANHUI`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_LIUHE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_SANHE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_BANHE` | 表旁给出组合与结果；结构命中不自动证明合化成立或吉凶解释。 |
| 暗合、通合、通禄合 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_ANHE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_TONGHE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_TONGLUHE`；{py:attr}`~bazi.school.BaziSchool.anhe_def` | {py:class}`~bazi.rules.DizhiRules.AnheDef` 列三读；`NORMAL` 暗合与通禄合给出相同组合，不是两份独立证据。 |
| 拱合、拱会与成立条件 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_GONGHE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_GONGHUI`、{py:attr}`~bazi.rules.DizhiRules.GONG_RELATIONS`、{py:attr}`~bazi.rules.DizhiRules.GONG_GONGHE_SCOPE`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_GONG_LU_TIANGAN`；{py:attr}`~bazi.school.BaziSchool.gong_def` | {py:class}`~bazi.rules.DizhiRules.GongheDef` 管结构，{py:class}`~bazi.rules.DizhiRules.GongDef` 保存同干、透化神、见禄字的完整来源档案。后者列现代来源与适用范围，不任意拼接成新读法。 |
| 刑 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_XING`；{py:attr}`~bazi.school.BaziSchool.xing_def` | {py:class}`~bazi.rules.DizhiRules.XingDef` 区分严格／宽松；按序查法可见方向，批量入口按多重集比较，不能混作同一方向语义。 |
| 冲、破、害 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_CHONG`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_PO`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_HAI` | 表旁给出无方向组合；没有专门的结构化来源关联。 |
| 地支生、克 | {py:attr}`~bazi.rules.DizhiRules.DIZHI_SHENG`、{py:attr}`~bazi.rules.DizhiRules.DIZHI_KE` | 只从地支五行派生，不考虑阴阳；五行的两个知识示例不覆盖地支间全部应用。 |

### 神煞

低层查法见 {py:mod}`~bazi.utils.shensha_utils`。表值及定义来源在 {py:class}`~bazi.rules.ShenshaRules`，锚点取值范围与出处在 `school.py` 的 `_ANCHOR_CHOICES`，分析器接入在 `analyzer/relationship.py` 的 `_REGISTRY`。固定锚点、被查位置和原局／流运使用范围还须读注册表及消费者，不能只看表值。

当前神煞知识对象为 `shensha.guoyin` 与 `shensha.kongwang`。其余行尚无同类专门对象，不等于全库文字从未提到这些名称。源码所列古籍、现代汇编与本仓署名也不因出现在下表就成为新的 `KnowledgeSource` 记录。

| 规则族 | 实现与配置 | 知识、出处与缺口 |
| --- | --- | --- |
| 桃花、红艳 | {py:attr}`~bazi.rules.ShenshaRules.TAOHUA`、{py:attr}`~bazi.rules.ShenshaRules.HONGYAN`；{py:attr}`~bazi.school.BaziSchool.hongyan_anchor` | 桃花注释分开表值与现代四柱查法；红艳记录乙一格分叉。红艳年干锚的出处缺口仍记在锚点表。 |
| 红鸾、天喜 | {py:attr}`~bazi.rules.ShenshaRules.HONGLUAN`、{py:attr}`~bazi.rules.ShenshaRules.TIANXI` | 表旁区分《星学大成》的宫限表值与现代查原局其余柱的用途。 |
| 驿马、华盖 | {py:attr}`~bazi.rules.ShenshaRules.YIMA`、{py:attr}`~bazi.rules.ShenshaRules.HUAGAI`；{py:attr}`~bazi.school.BaziSchool.yima_anchor`、{py:attr}`~bazi.school.BaziSchool.huagai_anchor` | 表旁与锚点说明分列；{py:meth}`~bazi.school.BaziSchool.mingli_tanyuan` 记录日锚档案，不把现代双锚合并成袁氏原法。 |
| 将星、灾煞 | {py:attr}`~bazi.rules.ShenshaRules.JIANGXING`、{py:attr}`~bazi.rules.ShenshaRules.ZAISHA`；{py:attr}`~bazi.school.BaziSchool.jiangxing_anchor`、{py:attr}`~bazi.school.BaziSchool.zaisha_anchor` | 表旁列《三命通会》与查法来源；不同字段支持的锚点集合分别取自锚点表。 |
| 劫煞、亡神 | {py:attr}`~bazi.rules.ShenshaRules.JIESHA`、{py:attr}`~bazi.rules.ShenshaRules.WANGSHEN`；{py:attr}`~bazi.school.BaziSchool.jiesha_anchor`、{py:attr}`~bazi.school.BaziSchool.wangshen_anchor` | 表旁说明绝位／临官位与出处；日锚、现代双锚的依据分列。 |
| 孤辰、寡宿 | {py:attr}`~bazi.rules.ShenshaRules.GUCHEN`、{py:attr}`~bazi.rules.ShenshaRules.GUASU` | 共用的表旁注释列规则与查法出处；解释层豁免不删除原始命中。 |
| 禄神、金舆 | {py:attr}`~bazi.rules.ShenshaRules.LUSHEN`、{py:attr}`~bazi.rules.ShenshaRules.JINYU`；{py:attr}`~bazi.school.BaziSchool.jinyu_anchor` | 禄神共用基础禄位表，金舆从禄位派生；出处见表旁，金舆的锚点依据另列。 |
| 魁罡、天赦 | {py:attr}`~bazi.rules.ShenshaRules.KUIGANG`、{py:attr}`~bazi.rules.ShenshaRules.TIANSHE` | 表旁列规则与出处，低层查法分别接收日柱、月令与日柱；原局分析器在 `_REGISTRY` 之外单独输出这两项整柱结果。 |
| 羊刃、飞刃 | {py:attr}`~bazi.rules.ShenshaRules.YANGREN`、{py:attr}`~bazi.rules.ShenshaRules.FEIREN`；{py:attr}`~bazi.school.BaziSchool.yangren_def`、{py:attr}`~bazi.school.BaziSchool.feiren_def` | {py:class}`~bazi.rules.ShenshaRules.YangrenDef` 分列子平、古禄命、帝旺三读与出处；两个字段独立，飞刃从相应羊刃表派生。 |
| 天乙贵人 | {py:attr}`~bazi.rules.ShenshaRules.TIANYI`；{py:attr}`~bazi.school.BaziSchool.tianyi_def`、{py:attr}`~bazi.school.BaziSchool.tianyi_anchor` | {py:class}`~bazi.rules.ShenshaRules.TianyiDef` 保存完整口诀／表档案；选择阳贵或阴贵不替调用方决定昼夜界线。 |
| 文昌 | {py:attr}`~bazi.rules.ShenshaRules.WENCHANG`；{py:attr}`~bazi.school.BaziSchool.wenchang_def`、{py:attr}`~bazi.school.BaziSchool.wenchang_anchor` | {py:class}`~bazi.rules.ShenshaRules.WenchangDef` 分列辛子／辛戌；表值、锚点与查找位置的来源边界分开保留。 |
| 文昌贵 | {py:attr}`~bazi.rules.ShenshaRules.WENCHANGGUI` | 表旁列全表与年干锚出处；它与文昌分列，不把同名近亲并成一个变体。 |
| 太极贵人 | {py:attr}`~bazi.rules.ShenshaRules.TAIJI`；{py:attr}`~bazi.school.BaziSchool.taiji_def`、{py:attr}`~bazi.school.BaziSchool.taiji_anchor` | {py:class}`~bazi.rules.ShenshaRules.TaijiDef` 保存壬癸两读、文字差异与戊己格矛盾；锚点依据另列。 |
| 国印贵人 | {py:attr}`~bazi.rules.ShenshaRules.GUOYIN`；{py:attr}`~bazi.school.BaziSchool.guoyin_def`、{py:attr}`~bazi.school.BaziSchool.guoyin_anchor` | {py:class}`~bazi.rules.ShenshaRules.GuoyinDef` 分开两表、锚点、查找位置与传抄限度；已有两条 `reference_only` 条目，见下方示例。 |
| 六甲旬空 | {py:attr}`~bazi.rules.ShenshaRules.KONGWANG`；{py:attr}`~bazi.school.BaziSchool.kongwang_anchor` | `shensha.kongwang.xunkong` 记基础二支，`.lookup` 记汇编转引与年日例，`.repository` 另记本库默认和范围；均为 `reference_only`。固定 revision 转录、下游白文、注释层与仓内政策分列，不把所引原书当作已见。详情查法见 {doc}`relations-transits`，不含单支筛选、截路、四大或解释层。 |

### 表外计算、配置与评估边界

{py:attr}`~bazi.school.BaziConfig.school` 选择整个流派档案。其余配置和纯计算规则不能从四个规则容器的属性清单中省略。

| 规则族／边界 | 实现与配置 | 知识、出处与缺口 |
| --- | --- | --- |
| 五行、干支循环 | {py:class}`~bazi.defines.Wuxing`、{py:class}`~bazi.defines.Ganzhi`；{py:func}`~bazi.utils.bazi_utils.ganzhi_of_year`、{py:func}`~bazi.utils.bazi_utils.ganzhi_of_day` | 五行两条本仓署名示例已存在；年／日干支计算有源码定义与基准日期，但尚无相应规则到知识来源的关联。 |
| 十神计算 | {py:func}`~bazi.utils.bazi_utils.shishen` | 已有 `shishen.*` 对象与定义条目，如 `shishen.bijian.definition`；定义条目不为地支取主气、藏干比例或全部解释作证，也不能由此假定十个对象都有默认定义条目。 |
| 四柱节界与换日 | {py:class}`~bazi.bazi.Bazi`；{py:attr}`~bazi.school.BaziConfig.precision`、{py:attr}`~bazi.school.BaziSchool.day_rollover` | {py:class}`~bazi.school.BaziPrecision`、{py:class}`~bazi.school.DayRollover` 与 {doc}`configuration` 说明边界。知识目录不是历法精度或换日出处目录。 |
| 胎元与命宫附加查询 | {py:attr}`~bazi.bazi_chart.BaziChart.taiyuan`、{py:attr}`~bazi.bazi_chart.BaziChart.minggong`；纯函数在 {py:mod}`~bazi.utils.bazi_utils` | `concept.taiyuan`、`concept.minggong` 区分月柱顺移、掌诀、中气按语、本库执行政策与待核候选，均为 `reference_only`。三百日胎元及其他命宫月界未编码；不扩四柱、配置或旧分析，计算不认证解释。用法见 {doc}`integration`。 |
| 历法、民用钟与真太阳钟 | {py:attr}`~bazi.school.BaziConfig.backend`；{py:class}`~bazi.calendar.backend.CalendarBackend`、`bazi/calendar/solar_time.py` 与地点输入 | 数据来源、精度及钟的边界见 {doc}`configuration` 和 {py:class}`~bazi.calendar.backend.CalendarBackend` 的说明。逐行历书／天文数据的独立定标不属本页评估；不因缺少知识条目就判计算无依据。 |
| 配偶星与配偶宫 | {py:attr}`~bazi.school.BaziSchool.peiou_xing_def`；{py:class}`~bazi.school.PeiouXingDef` 与 {py:class}`~bazi.bazi_chart.BaziChart` | 已有 `concept.peiou_xing`、`concept.peiou_gong` 及带原文来源的 `reference_only` 条目；历史读法、软件默认与适用条件仍须分别读取。 |
| 交运、小运、大运与流年 | {py:class}`~bazi.bazi_chart.BaziChart`；{py:attr}`~bazi.school.BaziConfig.dayun_year_rule` 与 {py:class}`~bazi.school.DayunYearRule` | 顺逆、间隔折算、物理时刻线与年份标签在源码说明中；当前没有相应专门知识对象。标签规则不能代替物理边界规则。 |
| 流运查询与关系组合 | {py:mod}`~bazi.transits`、{py:mod}`~bazi.utils.tiangan_utils`、{py:mod}`~bazi.utils.dizhi_utils`、{py:mod}`~bazi.analyzer.relationship` | 查询坐标、候选组合及原局／流运消费者各有语义；复用一张规则表不证明每种使用范围都有同一出处。 |
| 解释前提匹配 | {py:mod}`~bazi.context_matching` 与 {doc}`../catalog/criteria` | 已有可发现判据目录与知识引用；不等同于全库计算规则的来源索引，更不自动证明解释前提成立。 |

## 国印关联示例

两条国印知识已经存在，不需要再次录入。默认过滤与来源访问的通用用法见 {doc}`knowledge`。这里补上当前流派字段到条目、再到来源的查阅路径。

**下面的定义成员与条目 ID 对应是文档中的设计例子，不是库提供的规则关联接口。** 源码规则层不依赖 `KnowledgeBase`。

```{testcode} rule-coverage-guoyin
from bazi.defines import Tiangan
from bazi.knowledge import KnowledgeBase
from bazi.rules import BaziRules, ShenshaRules
from bazi.school import BaziSchool

kb = KnowledgeBase.load()
assert {obj.object_id for obj in kb.objects.values() if obj.kind == 'shensha'} == {'shensha.guoyin', 'shensha.kongwang'}
claims = {
  ShenshaRules.GuoyinDef.MODERN: 'shensha.guoyin.modern',
  ShenshaRules.GuoyinDef.WUXING_JINGJI: 'shensha.guoyin.wuxing_jingji',
}
for definition, claim_id in claims.items():
  school = BaziSchool(guoyin_def=definition)
  entry = kb.entry(claim_id)
  table = ShenshaRules.GUOYIN[school.guoyin_def]
  target = table[Tiangan.甲]
  offset = (target.index - BaziRules.TIANGAN_LU[Tiangan.甲].index) % 12
  assert all((table[tg].index - lu.index) % 12 == offset
             for tg, lu in BaziRules.TIANGAN_LU.items())
  # 对账当前条目措辞，不把解释文字当作结构化接口。
  assert f'偏移 +{offset}' in entry.text
  assert entry.limits
  source = kb.sources[entry.sources[0]]
  print(definition.name, school.guoyin_anchor.name, '甲见' + str(target))
  print(entry.claim_id, entry.source_state, entry.output)
  print(source.source_id, source.text_layer, source.state)
```

```{testoutput} rule-coverage-guoyin
MODERN YEAR_AND_DAY 甲见戌
shensha.guoyin.modern repository_attributed reference_only
repository_guoyin_variants editorial repository_attributed
WUXING_JINGJI YEAR_AND_DAY 甲见酉
shensha.guoyin.wuxing_jingji repository_attributed reference_only
repository_guoyin_variants editorial repository_attributed
```

这段代码只查表与知识，不创建命盘，也不执行“以哪柱查哪些位置”的命盘求值。三层支持要分别读：

| 层 | 当前事实从哪里取 | 来源边界 |
| --- | --- | --- |
| 表值 | `ShenshaRules.GUOYIN`、`GuoyinDef` 及条目文字 | 两表从禄位派生；定义说明区分原文、今人注释、抄本与现代读法，不合成一份无分歧的古籍证明。 |
| 锚点 | `BaziSchool.guoyin_anchor` 与 `_ANCHOR_CHOICES` 的对应注释 | 支持年锚、年日双锚；年干锚的明文出自今人注释，抄本表值见证不能证明该锚。 |
| 查找位置 | 定义 docstring、条目 `limits` 与实际消费者 | 果老文献的身命宫不等于四柱地支；本库四柱查法的现代来源与表值来源分开。 |

`repository_guoyin_variants` 概述的是本仓说明，`supports` 及 `limitations` 都应保留阅读。该来源引用固定的仓内快照；当前表与条目对账成功，不会把历史快照变成新增的古籍见证。

## 关联如何维护

- 计算表仍归 `rules.py`，默认与允许的配置归 `school.py`，知识文字、来源及状态归 `KnowledgeBase` 的注册表。禄神共表、金舆／国印派生等已有共享关系继续从源码取值，不在知识库或本页复制十格表。
- 不能从算法派生的原文、解释、锚点依据与支持限度继续独立保留。规则或文字变更时，对照条目 ID、定义成员、实际表值、锚点范围和消费者检查差异；上面的示例只校验当前两读的偏移与文字一致，不声称已自动维护全部语义。
- 覆盖表漏掉规则属性或配置字段，由文档测试的集合核对报告；引用与示例由严格构建及文档示例检查验证。这些检查不裁定命理依据，也不证明表外计算已经穷尽。
- 若将来增加可查询关联，建议先在知识侧验证一组“定义成员／配置字段 → 稳定条目 ID”的窄关联，保留表值、锚点、查找位置各自的支持来源。规则层不反向导入知识层，不把本页的手写对应直接宣布为公开接口。

## 评估结论与首批候选

| 项目 | 结论 | 后续条件 |
| --- | --- | --- |
| 国印两读 | 作为首个关联设计例子；保留现有条目与来源等级 | 运行时关联的归属、稳定标识和查询形状须另定；不借本页裁定传抄关系或改变查法。 |
| 五行生克 | 可作为下一组较小候选 | 现有两条只是本仓署名示例；扩展前先定是否只关联形式定义，不能直接升级为古籍见证或全体生克解释。 |
| 配偶星／宫 | 保留现有原文与前提边界，暂不作为机械关联的首个试点 | 先区分历史取法、默认计算、条件解释与消费者，不能把同对象的所有条目绑定为同一条计算规则。 |
| 全量规则查询 API、知识迁移 | 暂缓；本页不实施 | 先用小样本确认规则身份、关联所有者、维护成本与来源粒度，再确定实施范围；结构化知识缺口不等于每项都应新增解释。 |

新增来源或读法仍须分别确认系统归属、规则本身、锚点与查找对象。不同流派保留可选变体；来源未核或只有本仓署名的部分维持原状态，不因“已关联”就提高证据或默认输出资格。
