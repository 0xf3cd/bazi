知识条目
========

先读条文及其前提、限度，再沿来源链接查原文；登记信息保留全部其余字段。
来源状态、前提整理状态与默认展示是不同的选择，分别见
:py:data:`bazi.knowledge.SourceState`、:py:data:`bazi.knowledge.Applicability`
与 :py:attr:`bazi.knowledge.KnowledgeEntry.show_by_default`。

各项中的原始值可按下表阅读：

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - 字段
     - 值的含义
   * - 前提整理状态
     - ``unconditional``：无命盘前提；``described``：已记录前提文字；``unresolved``：前提待梳理。
   * - 来源状态
     - ``witnessed``：已核原文出处；``editorial``：原作说明；``unverified``：来源尚未核实；``repository_attributed``：仓内规则实现的归属。
   * - 默认展示
     - ``true``：纳入默认查询；``false``：仅供参考，须显式包含参考条目。

已记录前提文字不表示术语已有计算定义；完整状态说明与默认展示条件见 :doc:`../guides/knowledge`。

.. knowledge-catalog:: entries
