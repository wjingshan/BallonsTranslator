# 0008 收尾四条：控件本地化、整词不跨列、省略号、连续标点

- 日期：2026-10-20
- 状态：已验证（真实字体渲染 + 真实面板抓图）
- 相关提交：`feat(text): keep Latin words whole, collapse ellipsis runs, localize the new controls`

## 1. `Rotate Roman Words` 改中文、样式与周围一致

本机没有 Qt 的 `lrelease`（只有 `pylupdate6`），无法重新生成 `.qm`，所以新字符串
在中文界面下会显示英文。做法：`_localized(source, translated, chinese)` —— 仅当
「译文仍等于原文」且显示语言以 `zh` 开头时用中文兜底；已有词条永远优先。

| 原文 | 中文 |
| --- | --- |
| `Rotate Roman Words` | 西文整词旋转 |
| `Vertical Align` | 垂直对齐 |
| `Auto` / `Top` / `Centre` / `Bottom` | 自动 / 顶部 / 居中 / 底部 |

样式问题的根因是那个勾选框自带文字、走默认字体；改为**无文字勾选框 + `SmallParamLabel`**，
与其它行同字号（实测 9pt，与 `垂直对齐` 标签一致）。抓图核对：`_panel_shot.png`。

## 2. 西文单词不从中间断行

竖排换列判定原本只看「下一个格放不放得下」，于是 `master` 会从中间断开。
现在：多字母拉丁词的**首字符**用整词推进量判定（放不下就整词移到下一列）。
整词推进量用与逐字符循环相同的公式计算，包含开启旋转后的紧凑推进：

- `_roman_word_ends(text)`：纯函数，给出每个多字母词的 `start -> end`（可测）；
- `VerticalTextDocumentLayout._roman_word_advance()`：按同一公式累加。

真实字体验证：`天地master`（200×200，两字占 60，剩 140 放不下 180）→ 六个字母的列坐标
全为 `85.2`，且 `m` 位于列首（`y=0`）。词本身比列还高时（200×150）仍会断开，这是必然，
测试只要求不崩。

## 3. 省略号 `……` → `…`

`collapse_ellipsis_runs()` 把连续 `U+2026` 折叠成一个；`normalize_translation_punctuation()`
在 `postprocess_translations()`（「运行」完成时）同时改 `translation` 与 `rich_text`
（排版读的是 rich_text）。ASCII `...` 不动。

## 4. 连续标点放一行（无需改代码）

这是已有的「自动纵中横」功能，只是默认关闭。`apply_auto_tate_chu_yoko()` 在
`additional_chars='！？'`、`max_length>=3` 时会把 `！！！` 合成**一个** TCY 组：

```
'真的！！！' -> combine_ranges [(2, 3, ...)]
```

真实字体渲染中，三个 `！` 并排压在一格里（`_finish_compare.png` 中列）。

用户侧开启路径：设置 → 排版 → **自动纵中横** 勾选，**其他字符**填 `！？`
（`Automatic Tate-chu-yoko` 的中文词条已存在；`Max length` / `Include numbers` 无中文）。

## 测试

`tests/test_text_finishing_rules.py`（7 例）：词边界映射、整词不跨列、超列时不崩、
省略号折叠（含 rich_text）、重复标点合成一组、开关关闭时不改动。

## 上游可提交性

- 整词不跨列、省略号折叠：**适合**（通用排版正确性）。
- 控件文案：**已改为正规词条** —— 见下方补记。

## 补记：改用真正的 `.qm` 词条（已安装 lrelease）

本机原本没有 lrelease。装法：`pip install --target H:\DSH\workbench\_qttools PySide6-Essentials`
（82MB），只借用 `_qttools\PySide6\lrelease.exe`；应用环境仍是 PyQt6，不共处一个 `sys.path`。

随后只往 `zh_CN.ts` 的两个上下文各插入必要条目（**不用 `pylupdate6` 全量重排**，避免行号重写
产生巨大 diff），再用 lrelease 编译 `zh_CN.qm`（1190 条，0 未完成）。

校验：`QTranslator.load` 后 `translate('TextAdvancedFormatPanel', 'Rotate Roman Words')` 返回
「西文整词旋转」；真实字体抓图确认面板显示「垂直对齐 自动」，与「行距类型」同字号。

因此代码里已删掉运行时兜底 `_localized`，全部回到标准 `self.tr()`。其他语言暂无这七条词条，
会显示英文。`resources/` 不在上游补丁包路径内，随 fork 提交。

