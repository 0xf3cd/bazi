前提判据
========

判据目录可独立浏览。部分判据只检查前提的一部分事实，其限度与未实现部分随条目列出。

``entry_role='premise'`` 检查关联条目的完整前提；``entry_role='condition'`` 只检查局部事实，
不能据此认定条目全文前提成立。观察请求决定取哪些柱位或流运，判据本身不推断现实事件。

统一使用 :py:func:`bazi.context_matching.evaluate_context` 求值：必填 ``chart``、``criterion_id`` 和
``observation``，可选 ``knowledge`` 与 ``include_reference_only``。各项下方列出观察请求类及其范围，
点击类名可查构造参数；完整操作见 :doc:`../guides/integration`。
范围不完整或所需流运不可得时可能返回 ``UNKNOWN``，条件见
:py:attr:`bazi.context_matching.CriterionInfo.unknown_conditions`。

.. knowledge-catalog:: criteria
