# 同期历书中的 1929 年前节气日期与时间基准

## 结论

本批没有取得足以裁定 [issue #118](https://github.com/0xf3cd/bazi/issues/118) 的同期历书原页。五个目标中，只有 1911 立夏找到近同时代书籍所收的《大清宣統三年時憲書》线索；Google Books OCR 能定位题名、`都城順天府節氣時刻` 与 `立夏`，但目标行错乱，当前页面图像也不足以目视转录日期和时刻。1912 小寒、1912 寒露、1917 大雪、1927 白露均未核到可读的同期历书目标行。

香港天文台年报可以目视确认相邻时期的香港授时制度：1912 年报说明自 1913 年初以香港标准时间 13 时对应格林尼治平时 5 时；1917 年报同样把香港标准时间 13 时对应到格林尼治时间上午 5 时。这些材料证明的是 1913、1917 年香港授时服务采用 GMT+8，不是 HKO 后来制作的 1901–2100 公历农历对照表采用何种历史历书或归日基准。两者之间仍没有来源链。

因此，本批不支持在北京地方平时与 GMT+8 之间选择默认值，也不支持修改现有历法输出。未核到的栏位保持为空；OCR 不用于补字或换算。

## 证据口径

- **目视核图：**扫描页文字可直接辨认，允许转述该页明确写出的事实。
- **OCR-only：**搜索结果可帮助定位，但未取得足够清晰的页面图像；不据此转录目标日期、时刻或时间基准。
- **书目线索：**只证明某书、某版本或馆藏存在，不证明书中目标行的内容。
- **制度旁证：**证明同一时期某机构怎样授时，但没有材料把该制度连接到目标历书或 HKO 历史对照表。
- **未核到：**只表示本批所列检索范围内没有找到可用材料，不表示该材料不存在。

HKO 现行日期及其来源链另见 [`hko_provenance.md`](hko_provenance.md)。

## 五个目标

| 目标 | HKO 现行日期 | 同期历书目标行 | 日期与时刻 | 时间基准 | 当前判定 |
|---|---|---|---|---|---|
| 1911 立夏 | 1911-05-07 | Google Books `PP9` OCR 命中《大清宣統三年時憲書》所收节气表 | 未核 | 未核 | OCR-only；不可裁定 |
| 1912 小寒 | 1912-01-07 | 未核到 | 未核 | 未核 | 不可裁定 |
| 1912 寒露 | 1912-10-09 | 未核到 | 未核 | 未核 | 不可裁定 |
| 1917 大雪 | 1917-12-07 | 未核到 | 未核 | 未核 | 不可裁定 |
| 1927 白露 | 1927-09-08 | 未核到 | 未核 | 未核 | 不可裁定 |

HKO 年度文本只在相应日期列出节气名，没有时刻或时间基准：[1911](https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T1911c.txt)、[1912](https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T1912c.txt)、[1917](https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T1917c.txt)、[1927](https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T1927c.txt)。issue #118 中的午夜窗口与算法对拍值是检索目标，不是历史来源。

## 1911 时宪书线索

### Google Books 版本

Google Books 的《誰にも分かる暦の話：附最近三百餘年舊新歷對照表》署一戶直藏著、現代之科学社 1913 年出版；馆藏来源标为 University of California。[书目页](https://books.google.com/books?id=3xhSAQAAMAAJ)

该书 `PP9` 的搜索 OCR 有以下可定位锚点：

- `大清宣統三年歲次辛亥時憲書`
- `都城順天府節氣時刻`
- `立夏`

同一段 OCR 把日期、干支、时刻与相邻节气混在一起，出现 `立夏九十二日戊申寅正三刻四` 等无法可靠断句的文本。它不能证明立夏为哪一公历日，也不能证明原页实际写作何时。`都城順天府` 能定位表的适用地点，但没有在可核材料中给出子午线、相对格林尼治的时差或现代时区名称。[题名检索](https://books.google.com/books?jscmd=SearchWithinVolume2&q=%E5%A4%A7%E6%B8%85%E5%AE%A3%E7%B5%B1%E4%B8%89%E5%B9%B4%E6%AD%B2%E6%AC%A1%E8%BE%9B%E4%BA%A5%E6%99%82%E6%86%B2%E6%9B%B8&vid=3xhSAQAAMAAJ)；[表题检索](https://books.google.com/books?jscmd=SearchWithinVolume2&q=%E9%83%BD%E5%9F%8E%E9%A0%86%E5%A4%A9%E5%BA%9C%E7%AF%80%E6%B0%A3%E6%99%82%E5%88%BB&vid=3xhSAQAAMAAJ)

### 不能用 NDL 页面替代核图

国立国会图书馆 PID `1899256` 与 HathiTrust Record `100055361` 收录的是大鐙閣 1913 年 1 月版本；Google Books `3xhSAQAAMAAJ` 标为現代之科学社版本，不能假定两者是同一扫描。[NDL IIIF manifest](https://dl.ndl.go.jp/api/iiif/1899256/manifest.json)；[HathiTrust 书目](https://catalog.hathitrust.org/Record/100055361)

已目视检查的 NDL [canvas 5](https://dl.ndl.go.jp/api/iiif/1899256/R0000005/full/full/0/default.jpg) 是日本古历样张，不是 Google Books OCR 所指的宣统三年时宪书页。因此该图不能为 Google `PP9` 的 OCR 补字，也不能作为 1911 立夏的直接证据。翻案条件是取得 Google 版本 `PP9` 的清晰完整图像，或找到同一宣统三年时宪书的另一份可读扫描并核对版式。

## 中央观象台历书线索

### 《中華民國二年曆書》

HathiTrust Record `102360677` 收录敎育部中央觀象臺编《中華民國二年曆書》，北京出版，版权页纪年为民国元年 `[1912]`；实体说明为 `[ii, 80, 98]` 页，OCLC `502898700`。[HathiTrust 书目](https://catalog.hathitrust.org/Record/102360677)

这条记录证明中央观象台在 1912 年出版了供民国二年使用的历书，但题名所指年份是 1913。当前没有从该书核到 1912 小寒或寒露的目标行；出版年相同不能替代适用年证据。

### 《觀象歲書》

HathiTrust Record `100580511` 收录中央观象台《觀象歲書》，京華印書局 1915 年出版，共 `VIII, 363` 页，OCLC `35170991`。[HathiTrust 书目](https://catalog.hathitrust.org/Record/100580511)

Google Books `9oBFAQAAMAAJ` 的 OCR 把前言与说明书定位到以下规则：

- `PP11` 称相关时分使用北京地方平时。
- `PA320`、`PA321` 解释地方时、平时和以正午起算的天文日。

这些内容目前仍是 OCR-only，且出版于目标 1912 年之后。它能形成中央观象台曾使用北京地方平时与天文日记法的检索线索，但不能独自证明 1912、1917、1927 的历书沿用同一规则，更不能把天文日日期不经换算地当作民用日。[北京地方检索](https://books.google.com/books?jscmd=SearchWithinVolume2&q=%E5%8C%97%E4%BA%AC%E5%9C%B0%E6%96%B9&vid=9oBFAQAAMAAJ)；[天文日检索](https://books.google.com/books?jscmd=SearchWithinVolume2&q=%E5%A4%A9%E6%96%87%E6%97%A5&vid=9oBFAQAAMAAJ)

OCR 另有中央观象台经度数字，但未目视核图；本笔记不据此换算北京地方平时的精确 GMT 偏移，也不拿它校正 issue #118 使用的数值。

## 香港授时制度旁证

### 1912 年报

香港皇家天文台 1912 年度 Director's Report 由 Internet Archive 保存；馆藏元数据注明卷次 1912，并称出版物所标年份为 1913。[馆藏记录](https://archive.org/details/annualreportofdi1912honguoft)

- 印刷第 3 页说明气压、气温、蒸发和云量的逐时目视观测按 Hongkong local time 进行；该页没有定义这个词的 GMT 偏移。[第 3 页扫描](https://archive.org/download/annualreportofdi1912honguoft/page/n4.jpg)
- 印刷第 8 页说明，自 1913 年初，Blackheads Hill 报时球在工作日、星期日及政府假日均于香港标准时间 13 时落下，并在括号中对应为格林尼治平时 5 时。[第 8 页扫描](https://archive.org/download/annualreportofdi1912honguoft/page/n9.jpg)

后一点直接给出八小时差，但生效表述是 1913 年初；它不能反向证明 1912 年 1 月小寒或 10 月寒露所依据的中国历书采用 GMT+8。

### 1917 年报

1917 年度 Director's Report 的印刷第 10 页说明，Signal Hill, Kowloon 报时球每日于香港标准时间 13 时落下，并对应格林尼治时间上午 5 时。[馆藏记录](https://archive.org/details/annualreportofdi1917honguoft)；[第 10 页扫描](https://archive.org/download/annualreportofdi1917honguoft/page/n11.jpg)

印刷第 13 页还记录了一项未获采纳的夏令时建议：用东经 135° 子午线时间替代东经 120° 子午线时间，并以中国和菲律宾政府作相同变更为条件。[第 13 页扫描](https://archive.org/download/annualreportofdi1917honguoft/page/n14.jpg)

两页可以证明 1917 年香港授时服务的标准及当时对 120°/135° 子午线时间的讨论，但年报没有出现 1917 大雪，也没有说明 HKO 后来的历史历法表取材自这项授时服务。因此它们是制度旁证，不是节气事件证据。

这里使用 GMT/Greenwich Time，是因为原页使用的是当时术语；不把它改写成当时尚未采用的 UTC。

## 范围化负证据

截至 2026-09-24，本批作了以下可复核检索：

- 国立国会图书馆 OpenSearch 对《中華民國元年曆書》《中華民國六年曆書》《中華民國十六年曆書》作精确题名检索，三者均返回 `totalResults=0`。[元年](https://ndlsearch.ndl.go.jp/api/opensearch?title=%E4%B8%AD%E8%8F%AF%E6%B0%91%E5%9C%8B%E5%85%83%E5%B9%B4%E6%9B%86%E6%9B%B8)；[六年](https://ndlsearch.ndl.go.jp/api/opensearch?title=%E4%B8%AD%E8%8F%AF%E6%B0%91%E5%9C%8B%E5%85%AD%E5%B9%B4%E6%9B%86%E6%9B%B8)；[十六年](https://ndlsearch.ndl.go.jp/api/opensearch?title=%E4%B8%AD%E8%8F%AF%E6%B0%91%E5%9C%8B%E5%8D%81%E5%85%AD%E5%B9%B4%E6%9B%86%E6%9B%B8)
- Internet Archive 对同三个繁体题名作精确题名检索，均返回 `numFound=0`。[元年](https://archive.org/advancedsearch.php?q=title%3A%28%22%E4%B8%AD%E8%8F%AF%E6%B0%91%E5%9C%8B%E5%85%83%E5%B9%B4%E6%9B%86%E6%9B%B8%22%29&fl%5B%5D=identifier%2Ctitle%2Cdate%2Ccreator&rows=50&page=1&output=json)；[六年](https://archive.org/advancedsearch.php?q=title%3A%28%22%E4%B8%AD%E8%8F%AF%E6%B0%91%E5%9C%8B%E5%85%AD%E5%B9%B4%E6%9B%86%E6%9B%B8%22%29&fl%5B%5D=identifier%2Ctitle%2Cdate%2Ccreator&rows=50&page=1&output=json)；[十六年](https://archive.org/advancedsearch.php?q=title%3A%28%22%E4%B8%AD%E8%8F%AF%E6%B0%91%E5%9C%8B%E5%8D%81%E5%85%AD%E5%B9%B4%E6%9B%86%E6%9B%B8%22%29&fl%5B%5D=identifier%2Ctitle%2Cdate%2Ccreator&rows=50&page=1&output=json)
- HathiTrust 找到《中華民國二年曆書》《觀象歲書》及大鐙閣版《誰にも分かる暦の話》的书目和 Full view 记录，但本批没有从其页面服务取得四个民国目标事件的可读原页。
- 中国国家图书馆与台湾国家图书馆的公开目录在本批访问中未能稳定返回结果；因此本批不能对两馆馆藏作负断言。

这些精确题名零结果只约束所列目录和写法。历书可能使用干支年、简称、异体字、不同编纂机构或合订本题名；本批没有证明相关历书不存在。

## 翻案条件

以下任一材料都应触发重审：

- 1911 宣统三年时宪书可读原页，能同时核对书名、版式、立夏行和该表的时间记法。
- 中央观象台或其前后继机构供 1912、1917、1927 使用的历书原页，能直接看到小寒、寒露、大雪或白露行。
- 同册前言或说明书明确规定目标表采用的子午线、地方平时、标准时、天文日/民用日换算或时刻起算方法。
- HKO 官方材料明确说明 1901–1928 对照表是回算、抄录哪套同期历书，或怎样把节气时刻归入民用日期。

在取得上述材料前，1911 OCR、1915《觀象歲書》规则线索和香港年报授时记录应继续分列，不能拼接成一条不存在的来源链。
