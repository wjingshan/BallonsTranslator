# 0003 竖排西文整词旋转（紧凑）

- 日期：2026-10-20
- 状态：已验证
- 相关提交：见 `git log --oneline` 中 `feat(text): rotate Roman words as one compact run`

## 需求来源

用户在同一张漫画页上指出第二个问题：竖排里的英文 `Master` 被拆成「一格一个字母、
字母正立」，既难看又极占空间（占 6 个中文字的高度）。要求是「英文还是横向排列，
但摆放跟中文一样垂直」——即选项 A：整词旋转 90°，紧凑占位。

## 关键发现：紧凑推进的实现本来就有

`vertical_layout.py` 的每字竖向推进量在 `needs_vertical_rotation(char)` 为真时走
「旋转分支」：

```python
tbr_h = br.width() - (br.width() * 2 - cw2)   # 用双字测量还原真实横向推进
tbr_h += spacing_advance
```

也就是**旋转分支的格高就是字形的横向推进**，而不是一个 em。实测（真实 Windows
字体，30px，`letter_spacing=1.15`）：

| 字符 | 正立模式（现状）推进 | 旋转模式推进 |
| --- | --- | --- |
| M | 33.22 | 33.63 |
| a | 33.22 | 20.91 |
| s | 33.22 | 18.21 |
| t | 33.22 | 15.51 |
| e | 33.22 | 21.35 |
| r | 33.22 | 15.79 |

同一段文字（`怎么了，Master，你`）内容高度从 **369.8 → 295.8**（约 -20%），而中文与
标点的推进量完全不变。

因此不需要新增"合并 run"的排版机制：把拉丁字母导入已有的旋转分支即可，视觉上就是
整词旋转的效果（每个字母旋转、按横向推进紧密堆叠、按 capHeight 对齐基线）。

## 设计取舍

- 新字段 `FontFormat.roman_word_rotation: bool = False`，默认关闭，保持现状。
- **只作用于拉丁字母**：判定为 `char.isalpha() and _is_non_fullwidth_roman(char)`。
  原因：`_is_non_fullwidth_roman` 会把半角标点（`PUNSET_HALF`）也算作"罗马"，
  若直接复用会让英文逗号、感叹号一起旋转；数字（`DIGIT TWO`）与全角形式也不应旋转。
- **不改标点策略**：`standard_vertical_roman_alignment` 决定标点走哪套集合
  （`PUNSET_STANDARD_VERTICAL_ROMAN` / `PUNSET_VERNEEDROTATE`），本开关不参与，
  因此开启后括号、破折号、省略号的处理与之前一致。这正是不能直接让用户关掉
  「西文正立」的原因——那会连带改变标点行为。
- `centers_vertical_glyph()` 对启用本开关的字母返回 `False`，避免"既居中又旋转"
  的语义冲突（实际绘制走旋转分支，此处仅保持谓词自洽）。
- 切换时**必须重新排版**（`reLayout()`），不能像水平对齐那样平移已定列：紧凑推进
  会改变分列位置。`TextBlkItem.setRomanWordRotation()` 因此在竖排下走完整重排。
- 横排下该字段只存储、不生效（排版器不读），并在单测中断言横排几何完全不变。

## 改动文件

| 文件 | 改动 |
| --- | --- |
| `ballontranslator/utils/fontformat.py` | `roman_word_rotation` 字段与非法值回退 |
| `ballontranslator/ui/text_engine/vertical_layout.py` | `roman_word_rotation_applies()`；`needs_vertical_rotation()` 与 `centers_vertical_glyph()` 接入 |
| `ballontranslator/ui/text_engine/item.py` | `TextBlkItem.setRomanWordRotation()` |
| `ballontranslator/ui/text_engine/formatting/commands.py` | `ffmt_change_roman_word_rotation()`（可撤销，一次一步） |
| `ballontranslator/ui/text_engine/formatting/advanced.py` | 「Rotate Roman Words」勾选框与同步 |
| `doc/ui/text_layout.md` | 维护者契约：开关语义、为何重排、为何不动标点 |
| `tests/test_text_roman_word_rotation.py` | 14 个用例 |

## 验证

- 新增 `tests/test_text_roman_word_rotation.py`：**14/14 通过**。覆盖开关只作用于字母
  （数字/半角标点/全角形式不变）、关闭时仍正立且居中、开启时字母走旋转分支且推进与
  「全旋转模式」完全一致、标点与中文推进不变、内容高度不增加、窄框分列后字母仍旋转、
  横排几何完全不变、实时切换与新建一致、重复设置幂等、命令注册与 undo 往返、序列化、
  非法值回退。
- 真实字体渲染对比（默认 Windows 平台，非离屏）：三种模式各渲染一张 PNG 并逐字符
  比对推进量；`standard=True + 开关` 与 `standard=False` 的字母推进完全相同，
  与 `standard=True` 的标点推进完全相同。
- 回归：`tests.test_vertical_alignment`、`test_text_engine_cache`、
  `test_horizontal_whitespace`、`test_vertical_japanese_punctuation`、
  `test_vertical_combined_whitespace` 共 28 例 → 与本改动前基线一致（同样 3 个
  既有失败）。`tests.test_vertical_roman_alignment` 36 例 → 与本改动前基线一致
  （同样 7 个既有失败，均与本改动无关）。
- 面板离屏冒烟：默认未勾选、`set_active_format` 同步、程序化同步不发信号、
  用户点击发出 `('roman_word_rotation', True)`。
- `py_compile` 通过；doctest 63 例 0 失败；`git diff --check` 干净。

### 未验证 / 限制

- **离屏环境没有任何字体**（`QFontDatabase.families()` 为 0，所有字形按 em 方块处理），
  因此单测只能断言结构与分支，不能断言像素级外观。视觉证据来自真实平台渲染的 PNG。
- **没有在运行中的程序里点击过这个勾选框**（需重启程序加载新代码）。用户实例
  PID 18232 仍在跑旧代码。
- **未做主题化真机走查**：勾选框样式沿用现有 QSS（`TextAdvancedFormatCheckbox`
  没有专门规则），深色主题下的观感未验证。
- 新增的两个 `tr()` 字符串（`Vertical Align`、`Rotate Roman Words`）**没有中文翻译**，
  中文界面下会显示英文。上游的翻译由 `resources/translate/` 单独维护，未在本改动中加入。

## 上游可提交性

**需改造**：功能通用、默认行为不变、不引入新依赖，方向适合上游。提 PR 前需要：

1. 与作者确认命名与 UI 位置：这个开关与既有「西文正立」是并列关系（一个管字母、
   一个管标点集合），组合起来共四种状态，可能需要合并成一个更清晰的三态/四态选项。
2. 补中文翻译条目。
3. 若上游希望「整词旋转」成为竖排西文的默认，则要处理已有项目的迁移。
