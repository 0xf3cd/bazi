# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

# Independent literal rosters: never derive these exclusions from the corpus being checked.
AUXILIARY_OBJECT_IDS = ('concept.taiyuan', 'concept.minggong')
AUXILIARY_SOURCE_IDS = (
  'youyilu.taiyuan_minggong', 'sanming_tonghui.taiyuan', 'sanming_tonghui.minggong',
  'mingli_tanyuan.minggong', 'repository.taiyuan_minggong',
)
AUXILIARY_ENTRY_IDS = (
  'concept.taiyuan.month_shift', 'concept.taiyuan.three_hundred_days', 'concept.taiyuan.repository',
  'concept.minggong.palm', 'concept.minggong.zhongqi',
  'concept.minggong.month_boundary_candidates', 'concept.minggong.repository',
)
AUXILIARY_WITNESSED_IDS = (
  'concept.taiyuan.month_shift', 'concept.taiyuan.three_hundred_days',
  'concept.minggong.palm', 'concept.minggong.zhongqi',
)

SHENSHA_OBJECT_IDS = (
  'shensha.tianyi', 'shensha.taohua', 'shensha.yima', 'shensha.wenchang', 'shensha.huagai', 'shensha.yangren',
)
SHENSHA_SOURCE_IDS = (
  'sanming_tonghui.tianyi.yinyang', 'sanming_tonghui.taohua.table', 'sanming_tonghui.yima.table',
  'sanming_tonghui.huagai.table', 'sanming_tonghui.yangren.luming', 'sanming_tonghui.yangren.ziping',
  'xingxue_dacheng.wenchang_xin_xu',
  'wenzhen_shensha.tianyi', 'wenzhen_shensha.taohua', 'wenzhen_shensha.yima',
  'wenzhen_shensha.wenchang', 'wenzhen_shensha.huagai', 'wenzhen_shensha.yangren',
  'click2macao.tianyi_geng_with_xin',
)
SHENSHA_ENTRY_IDS = (
  'shensha.tianyi.yinyang', 'shensha.taohua.table', 'shensha.yima.table', 'shensha.huagai.table',
  'shensha.yangren.luming', 'shensha.yangren.ziping', 'shensha.wenchang.xin_xu',
  'shensha.tianyi.lookup', 'shensha.taohua.lookup', 'shensha.yima.lookup',
  'shensha.wenchang.lookup', 'shensha.huagai.lookup', 'shensha.yangren.lookup',
  'shensha.tianyi.geng_with_xin',
)

BACKFILL_SOURCE_IDS = ('guoguan_wenhua.tiangan_personality', 'ditiansui.bing_frost_snow')
BACKFILL_ENTRY_IDS = (
  'legacy.tiangan.jia.personality', 'legacy.tiangan.yi.personality', 'legacy.tiangan.bing.sociability',
  'legacy.tiangan.ding.personality', 'legacy.tiangan.wu.personality', 'legacy.tiangan.ji.personality',
  'legacy.tiangan.geng.personality', 'legacy.tiangan.xin.personality', 'legacy.tiangan.ren.personality',
  'legacy.tiangan.gui.resourcefulness', 'legacy.tiangan.bing.frost_snow_image',
)

FOLLOWUP_SOURCE_IDS = ('dayi.tiangan_bing_personality', 'laoshenpo.geng_regulated_transit')
FOLLOWUP_ENTRY_IDS = ('legacy.tiangan.bing.impatience', 'legacy.tiangan.geng.regulated_transit')
