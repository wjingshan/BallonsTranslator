# 0016 合并上游 v1.5.24

- 日期：2026-11-26
- 状态：**已验证**
- 上游可提交性：—

## 上游 v1.5.24 的变化

- **气泡约束的文本块新增旋转手柄**：手柄挂在轮廓外侧（带引线），拖动可整体旋转；
  轮廓被裁切、被视口遮挡时会自动换边或隐藏，旋转中保持抓取点不脱离
- 画布快捷键 `O` 绑定图层透明度（仅文本编辑模式下生效）
- 韩语本地化更新（`ko_KR.ts/.qm`）
- 内部重构：`shape_control` 统一由 `owner.blk_item` 取当前文本块，
  移除 `BubbleShapeControl.bind()` / `_bound_item`；画布统一调用 `cancelDrag()`；
  `_segment_rect_entry` 迁到 `misc.segment_rect_interval`；
  旋转命令 `RotateItemCommand` 改为 `(item, 起始角度)` 列表

规模：5 提交 / 26 文件 / +1554 −949；试合并冲突 4 文件。

## 冲突与解决

| 文件 | 冲突性质 | 解决 |
| --- | --- | --- |
| `pyproject.toml` | 版本号同行 | 取 `1.5.24` |
| `ui/mainwindow.py` | 同一行 `auto_textlayout_flag` 表达式 | 保留本地 `not inpaint_only` 守卫，其余随上游 |
| `text_engine/vertical_layout.py` | 同一处 `char_records.get` 取值（双方各自写过） | 合并为一次取值 + 本地注释 |
| `text_engine/shape_control.py` | 上游删掉 `bubble_control.bind(blk_item)`，本地保留 `_notify_quick_actions()` | 保留 `_notify_quick_actions()`，删除 `bind` 调用（上游已改为 `owner.blk_item`） |

## 无标记但需人工处理的点

- `tests/test_vertical_interaction.py`：本地 0015 手工移植的两条 IME 用例与上游同名用例**重复出现**，
  删除本地副本，保留上游版本（断言更紧凑）；`ア` 探测列容量的本地修正保留
- `bubble_control.py`、`shape_control.py` 判定：本地在这两个文件相对 v1.5.22 只多了
  `_notify_quick_actions` 与 `bind` 两处，因此整体采用上游重构；合并后
  `shape_control.py` = 上游 + 3 行本地快捷手柄同步，`bubble_control.py` = 上游
- `canvas.py` / `manager.py` / `panel.py` / `commands.py` / `misc.py` / `mainwindowbars.py`：
  改动行数与上游逐文件完全一致（本地此前未分歧），无需手工合入

## 本地自研功能核查（合并后仍在）

`no_forced_wrap`（38 处）、`push_no_forced_wrap`（6）、`_apply_no_forced_wrap_items`（2）、
`ffmt_change_vertical_alignment`（2）、`manual_font_size`（16）、`font_size_outlier_ratio`（4）、
`setVerticalAlignment`（10）：与合并前计数一致；`bubble_layout` 由 64 增至 68（上游旋转手柄）。

## 验证

- `test_vertical_interaction`(15) / `test_bubble_editing`(27) / `test_bubble_layout`(51) /
  `test_text_transform_undo`(113) / `test_text_quick_actions`(22) / `test_adaptive_wrap_layout` /
  `test_font_size_editing` / `test_text_finishing_rules` / `test_text_roman_word_rotation`：282 例，7 失败
- 另跑 15 个画布/竖排模块单模块：`test_text_style_shortcuts`、`test_brush_lines`、`test_shape_fill`、
  `test_canvas_cursor_lifecycle`、`test_canvas_stroke_lifecycle`、`test_canvas_inpaint_lifecycle`、
  `test_editing_layer_opacity`、`test_vertical_font_fit`、`test_vertical_combined_whitespace`、
  `test_vertical_japanese_punctuation`、`test_vertical_hangul`、`test_vertical_roman_alignment`、
  `test_vertical_alignment` 等
- 所有失败在 `HEAD` 的独立 worktree 上逐条复现，属本机字体度量/临时目录既有问题：
  `test_bubble_layout` 4 例、`test_vertical_alignment` 1 例、`test_text_transform_undo` 2 例、
  `test_vertical_hangul` 2 例、`test_vertical_roman_alignment` 7 例、
  `test_canvas_inpaint_lifecycle` 1 例，**无新增回归**
- `compileall` + 导入通过；`canvas.toggle_layer_opacity` → `bottomBar.toggle_layer_opacity` 连线完整

## 已知遗留

- `tests/test_canvas_save_state` 在本机 Qt 上仍触发 `0xC0000409` 崩溃（合并前后一致）
- 上游旋转手柄的实际手感（引线避让、视口裁切）需真机目视验收，本轮只做静态与单测验证
