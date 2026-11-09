# 0013 手动字号不被载入期自动放大覆盖

- 日期：2026-11-09
- 状态：**已验证**
- 上游可提交性：适合（与合并后的 v1.5.21 基线一致）

## 症状

手动改过文字大小/排版后，切到其他页再切回来，**有时**某些文字块的字号和版式
退回修改前的样子；而且同一块来回翻几次会一次比一次大。

## 根因

`SceneTextManager.populateSceneTextitems()` 每次重建文字块时都会执行可选的
「竖排自动放大」：

```python
if (pcfg.vertical_font_autofit_enabled and pcfg.let_fntsize_flag == 0
        and blk_item is not None and textblock.vertical):
    fit_vertical_font_size(blk_item)
```

`fit_vertical_font_size()` 只判断「文字是否填满框」（`_FULL_FRACTION = 0.9`），
上限 1.6 倍，**不区分字号是不是用户手动选的**。用户把字号改小、或把框还原后，
框里留出空隙，翻页重载就把它重新放大回填；放大后的值又在保存时写回 `blk`，
于是逐轮滚雪球。

这也解释了「有时才回退」：只有框里有余量的块才会触发（`blk9` 框高只有 1px
余量，10 次往返 0 次回退）。

## 修复

新增持久化标记 `TextBlock.manual_font_size`（沿用 `pre_free_wrap_rect` 的做法，
随 `vars()` 序列化，老工程缺键默认 `False`），只在用户主动改字号的三类入口置位：

| 入口 | 位置 |
| --- | --- |
| 面板字号框 / 相对字号 / 全局样式 | `formatting/commands.py` 的 `ffmt_change_font_size`、`ffmt_change_rel_font_size` |
| 面板大小拖拽 / 步进 | `formatting/size_edit_session.py` 的 `ResizeTextItemsCommand.redo` |
| `T` 手柄拖拽结束 | `text_quick_actions.py` 的 `end_scale` |

`populateSceneTextitems()` 的自动放大条件加上 `and not textblock.manual_font_size`。

口径选择：没有关掉自动放大（会砍掉流水线新块的自动填框），也没有在 `setFontSize()`
里统一置位（流水线 `layout_textblk` 也走这条，会把功能整体废掉）。

## 验证

同一份代码做 A/B（只切换该标记），5 块 × 10 次翻页往返，按块身份匹配：

| 块 | 载入 | 编辑后 | 旧行为 第1次 | 旧行为 第10次 | 修复后 |
| --- | --- | --- | --- | --- | --- |
| blk0 | 152.70 | 106.89 | 170.02 | 226.70 | 106.89 |
| blk3 | 156.49 | 109.54 | 144.46 | 192.62 | 109.54 |
| blk7 | 72.00 | 50.40 | 80.17 | 106.89 | 50.40 |
| blk9 | 95.00 | 66.50 | 66.50 | 66.50 | 66.50 |
| blk12 | 77.00 | 53.90 | 53.90 | 53.90 | 53.90 |

- 合计：**修复前 30/50 字号回退、30/50 框变化；修复后 0/50、0/50**
- 面板字号框路径：修复前 2/5 → 修复后 0/5
- 关闭 `vertical_font_autofit_enabled` 时同样 0/5，确认与开关强相关
- 只拖 `T` 不点 `↵`：0/5（该手势框与字一起缩放，框仍被填满）
- 单元测试：107 例通过（含新增 2 条回归）

## 未处理

自由换行「贴合」后重载，框高仍会多约 11px（75×341 → 76×352.2 → 76×353，
字号不变），属于布局 maxsize 重算的既有差异，量级远小于本次症状，未扩大改动面。

## 复现脚本

`tmp/` 下保留了 `repro_c91.py`、`verify_flow.py`、`probe_*.py` 及日志，
可直接复跑；`input/` 素材未被写入。
