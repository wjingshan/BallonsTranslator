# 0015 手工移植上游 v1.5.23 的三条修复

- 日期：2026-11-22
- 状态：**已验证**
- 上游可提交性：适合

## 上游 v1.5.23 的范围

`v1.5.22..v1.5.23` 共 3 提交 / 8 文件 / +235 −33：

| 提交 | 主题 |
| --- | --- |
| `820ebb51` | 翻译失败/译文为空时不再收缩文本框（跳过自动排版） |
| `4158a54b` | 输入法组字（IME preedit）时竖排文字崩溃 |
| `4f70a427` | 自动排版前刷新段落度量（#1393 横排分多行崩溃），版本号 1.5.23 |

## 本分支的落点

三条问题在本地全部存在（部分是本分支改写过同名区域，属"语义相同、代码位置不同"）：

1. `vertical_layout.py` 取列宽改为 `record = char_records.get(char_idx, {})` +
   `record.get('line_width', -1)`，与紧随其后的 `record` 取值合并为一次。
   本地原有的合并标点/落脚列宽逻辑保持不变。
2. `editing/manager.py` 的 `restore_charfmts`：
   - 用 try/finally 保存并恢复 `relayout_on_changed` / `repaint_on_changed`；
   - 分段比对增加 `half_len(original)`（分词可能把标点改窄）；
   - 结尾由 `layout.reLayout()` 改为 `layout.reLayoutEverything()`，
     因为撤销命令把 Qt 的 `documentChanged` 推迟到 squeeze 之后。
3. `proj_imgtrans.get_page_progress(pagename, finish_code=None)` 支持按单个阶段位检查；
   `mainwindow.on_pagtrans_finished` 先算 `translation_failed`（只看 `FIN_TRANSLATE`），
   失败则不做自动排版、不做 legacy 收缩，跳过条件改为
   `not translation.strip() or not get_text().strip()`。
   本地原有的 `not inpaint_only` 守卫保留（上游该提交把它去掉了）。

## 与本地自研功能的关系

- 自由换行（`no_forced_wrap` / ↵ 手柄）、气泡约束（`bubble_layout`）都在
  `toggle_text_layout` 的跳过条件里，本次改动只在其外层加"翻译是否失败"判断。
- 竖排框内对齐、整词不跨列、T 手柄缩放、原图比对、整页放大镜均未改动。

## 顺带修正的本地测试

`test_left_right_moves_between_vertical_columns` 用 121 个 `A` 探测列容量，
但本地"整词不跨列"设计会把整段拉丁串当成一个词（`test_text_finishing_rules`
的 `test_word_taller_than_the_column_overflows_whole` 明确要求整词溢出），
两者互斥。改为用片假名 `ア` 探测——片假名按字符断列，与设计一致，
测试断言 `[40,40,40,1]` 不变。

## 验证

- `tests.test_vertical_interaction` + 上游移植的两条 IME 用例：15 例通过。
- `tests.test_text_finishing_rules`、`tests.test_text_roman_word_rotation`：全部通过。
- 本地 9 个排版相关模块批量跑：130 例，5 失败 + 3 错误，与改动前基线逐条一致
  （`test_bubble_layout` 字体度量 4 例、`test_vertical_alignment` 1 例、
  `test_proj_imgtrans_translation_context` 的 Temp 目录 PermissionError 3 例）。
- `tests.test_canvas_save_state` 在本机 Qt 上会触发 `0xC0000409` 崩溃，
  改动前后同样如此，属环境既有问题，未纳入回归。

## 未移植

- 上游新增的 `tests/test_canvas_save_state.py` 124 行用例（该模块在本机崩溃，无法验证）。
- `doc/ui/text_layout.md` 只同步了反排段落的措辞，其余上游文档表述未动。
