# 0002 文字框内垂直对齐（顶/中/底）

- 日期：2026-10-20
- 状态：已验证
- 相关提交：见 `git log --oneline` 中 `feat(text): add frame vertical alignment`

## 需求来源

用户提供的漫画页（`Master` 与中文混排的竖排气泡）中，译文贴不到气泡中间：文字从气泡
上沿开始排列、底部甚至溢出。用户还指出这是竖排状态下的普遍现象。

## 根因（不是"差一点没对准"）

1. **竖排下自动排版整条链路被关闭**：`editing/manager.py:891` 在竖排时直接
   `return`，函数 docstring 自承 `vertical writing is not supported yet`。因此竖排
   既不会自动缩字号，也不会把文字摆到中间。
2. **`FontFormat` 只有水平 `alignment`，没有垂直锚点字段**，布局无处读取垂直意图。
3. **横排的垂直居中原本存在，但硬绑在 `alignment == AlignCenter` 上**
   （原 `horizontal_layout.py:923-934`），没有独立开关，也无法单独表达"顶对齐但水平居中"。

## 设计取舍

- 新增 `TextVerticalAlignment`：`Auto(-1) / Top(0) / Center(1) / Bottom(2)`，
  字段 `FontFormat.vertical_alignment`，默认 `Auto`。
- **`Auto` 完全复现历史行为**：横排在水平居中对齐时才垂直居中，竖排保持顶对齐。
  这样已有项目和页面在升级后不会整体位移，符合 `AGENTS.md`"保留行为"的约束；
  用户显式选择后才改变。
- **锚点在排版完成后作为"整行平移"应用**，不进入换行决策。原因：竖排的换行/分列
  判定用绝对 y 与 `available_height` 比较，若把起点下移会让每列少排字、导致内容变高，
  结果不是纯平移。先按原样排版、再整体平移，才能保证换行不变。
- 竖排布局除行位置外还存了**绝对竖直格**
  （`line_spaces_lst[b][l][2]` 的 y 列表、`y_offset_lst[b]` 的 `[top, bottom]`），
  它们供选区格、格删除、Ruby 摆放和 Glyph Slant 绘制使用。因此平移必须同时移动这些
  记录，否则"画在哪"与"点到哪"不一致。这是本次改动最容易出错的地方，已单测覆盖。
- 横排原公式 `(max_height - new_height)/2 - doc_margin` 统一改为
  `(available_height - content_height)/2`。二者在 `doc_margin = 0`（无文字特效内边距）
  时完全一致；仅当有特效内边距时新公式把内容放正，旧公式会偏高 `doc_margin/2`。
- UI 放在已有的「高级文字格式」折叠面板（`text_advanced_format_panel`），
  选项 `Auto / Top / Centre / Bottom`。未加入主工具栏：那里已有 3 个对齐按钮 +
  格式组 + 3 个勾选器，再加 3 个图标按钮会挤爆固定宽度侧栏。

## 改动文件

| 文件 | 改动 |
| --- | --- |
| `ballontranslator/utils/fontformat.py` | `TextVerticalAlignment` 枚举；`vertical_alignment` 字段与非法值回退（警告 + `Auto`） |
| `ballontranslator/ui/text_engine/layout.py` | `effective_vertical_alignment()`、`vertical_anchor_shift()`、`translate_lines_y()` |
| `ballontranslator/ui/text_engine/horizontal_layout.py` | 用锚点取代硬绑 `AlignCenter` 的垂直居中 |
| `ballontranslator/ui/text_engine/vertical_layout.py` | 排版后按锚点平移，新增 `_translate_absolute_y()` 同步绝对竖直格 |
| `ballontranslator/ui/text_engine/item.py` | `TextBlkItem.setVerticalAlignment()` |
| `ballontranslator/ui/text_engine/formatting/commands.py` | `ffmt_change_vertical_alignment()`（可撤销，一次一步） |
| `ballontranslator/ui/text_engine/formatting/advanced.py` | 「垂直对齐」下拉框、状态同步与信号 |
| `doc/ui/text_layout.md` | 维护者契约：锚点语义、平移时机、绝对格必须同步 |
| `tests/test_text_vertical_anchor.py` | 15 个用例 |

## 验证

环境：`ballontrans_pylibs_win\python.exe`，`QT_QPA_PLATFORM=offscreen`。

- 新增 `tests/test_text_vertical_anchor.py`：**15/15 通过**。覆盖
  `Auto` 的历史规则、四档锚点在横竖排的实际位移量（内容 150 在 300 框内：Center
  ≈75、Bottom ≈150）、换行与矩形尺寸不变、绝对竖直格跟随行位置、
  同一屏幕点在两档锚点下落到不同字符（命中跟随）、切换与新建结果一致、
  重复设置同一值幂等、序列化往返、非法值回退、命令层经 undo 栈应用与撤销。
- 回归：`tests.test_vertical_alignment`、`test_text_engine_cache`、
  `test_horizontal_whitespace`、`test_vertical_japanese_punctuation`、
  `test_vertical_combined_whitespace` 共 28 例，**与本改动前的基线完全一致**
  （仓库在同一台机器上暂存改动后复跑，失败的仍是同样的 3 个用例：
  `test_switching_alignment_translates_layout_and_preserves_hits`、
  `test_overflowing_spaces_consume_a_row_before_following_text`、
  `test_selection_uses_relocated_space_cells`；属既有字体环境问题，非本次引入）。
- 面板控件离屏冒烟：4 档数据 `-1/0/1/2`、`set_active_format` 与
  `set_vertical_alignment` 双向同步、变更发出 `('vertical_alignment', 1)`。
- `py_compile` 全部改动文件通过；`git diff --check` 干净。

### 未验证 / 限制

- **没有做主题化真机走查**：离屏环境无法渲染主题，控件的配色/排版只在构造路径上验证。
- **没有在运行中的程序里点过这个下拉框**（改动需重启程序生效）。用户实例 PID 18232
  在改动前已运行，仍为旧代码。
- 竖排「字号自动适配」仍未实现（见下），因此**本改动只解决"贴不到中间"，不解决
  "字太大装不下"**。

## 顺带发现的既有缺陷（未修，留作后续）

竖排的放大判定用的是 `min_height`：

```python
if self.min_height - doc_margin > self.available_height:   # vertical_layout.py
```

但 `min_height` 只在 Ruby 分支里被赋值（`vertical_layout.py` 中 3 处），普通竖排
文本恒为 0，因此该判定永不触发。真正的内容高度存在 `shrink_height`。后果：竖排内容
超出文本框时不会放大框，直接溢出气泡——正是用户截图中"底部被切掉"的表现。
本次改动把 `shrink_height` 用于锚点计算，但**未改**上述判定与横排的差异，
因为那属于「竖排自动排版」范畴（上游明确未支持），需要单独一次改动。

## 上游可提交性

**需改造**：垂直锚点是通用排版能力、默认行为不变、不引入新依赖，方向适合上游。
但提 PR 前需要：

1. 决定是否把 `Auto` 这套"历史规则"折成默认值（上游可能更愿意直接默认顶对齐，
   历史耦合由迁移处理）。
2. 补一条与 `test_switching_alignment_*` 同类的竖排命中回归，覆盖绝对格同步。
3. UI 是否放进高级面板需要与作者确认（上游也许希望放主工具栏）。

另外「竖排自动排版缺失」与「`min_height` 死路径」是独立的上游 bug，值得单独报。
