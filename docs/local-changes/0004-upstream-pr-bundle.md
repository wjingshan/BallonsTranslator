# 0004 上游提 PR 用的干净改动包

- 日期：2026-10-20
- 状态：已验证
- 作用：把本地两个排版改动整理成可直接发给作者的形态，并与本地记录分离

## 为什么需要这一步

`master` 上的提交混了两类内容：**上游需要的**（代码、维护者文档 `doc/ui/text_layout.md`、
测试）和**只属于本机的**（`docs/local-changes/` 记录目录）。后者按本目录 `README.md`
的约定不应出现在给作者的 PR 里。因此单独切一条分支承载"可发送"内容。

## 分支

`upstream-pr`，基于上游基线 `fa3e137 release v1.5.20`，两个提交：

| 提交 | 内容 |
| --- | --- |
| `c0e64f0` | `feat(text): add frame vertical alignment (top/centre/bottom)` |
| `02a361c` | `feat(text): rotate Roman words as one compact run in vertical layout` |

该分支只触及 10 个文件：`ballontranslator/`（7）、`doc/ui/text_layout.md`、
`tests/test_text_vertical_anchor.py`、`tests/test_text_roman_word_rotation.py`。
`docs/local-changes/` 完全不在其中。

`master` 与 `upstream-pr` 在 `ballontranslator/ doc/ tests/` 上内容一致（已用
`git diff master upstream-pr -- ballontranslator doc tests` 验证为空）。

## 改动包

位置：`H:\DSH\workbench\ball-upstream\`

| 文件 | 用途 |
| --- | --- |
| `0001-feat-text-add-frame-vertical-alignment-top-centre-bo.patch` | 垂直对齐 |
| `0002-feat-text-rotate-Roman-words-as-one-compact-run-in-v.patch` | 整词旋转 |
| `full.diff` | 两个改动的单一合并 diff（便于先整体浏览） |
| `PR.md` | 英文 PR 说明：动机、行为约定、文件/符号表、验证、未覆盖项、发现的上游缺陷、待作者决定的问题 |

**补丁有序**：`0002` 依赖 `0001`（两者在 `item.py`、`advanced.py` 上共享上下文），
单独只发一个需要重新生成。

## 重新生成

```bash
git checkout -B upstream-pr fa3e137
git checkout c0e64f0 -- ballontranslator doc tests   # 或按提交顺序重建
git checkout master  -- ballontranslator doc tests
git format-patch fa3e137..upstream-pr -o /path/to/ball-upstream --numbered --suffix=.patch
git diff fa3e137..upstream-pr -- ballontranslator doc tests > /path/to/ball-upstream/full.diff
```

更稳的做法是直接复用现有分支：只要 `master` 上这两个功能没有新改动，
`upstream-pr` 的内容就等于 `master` 去掉 `docs/local-changes/`。

## 如何验证补丁能干净套用

在不污染主仓库的前提下用临时 worktree 回放：

```bash
git worktree add --detach /tmp/bt-baseline fa3e137
cd /tmp/bt-baseline
git am /path/to/ball-upstream/0001-*.patch /path/to/ball-upstream/0002-*.patch
git diff upstream-pr --stat        # 必须为空
git worktree remove --force /tmp/bt-baseline
```

本次已验证：回放成功、与 `upstream-pr` **零差异**、无空白字符警告
（首次回放时报过一次 "new blank line at EOF"，来源是
`tests/test_text_vertical_anchor.py` 末尾多一个空行，已由 `8e78a64` 修正后重新导出）。

## 验证记录

在该分支上运行（`ballontrans_pylibs_win\python.exe`，离屏）：

- `tests.test_text_vertical_anchor` + `tests.test_text_roman_word_rotation`：
  **30 例全通过**。
- 既有相关套件：`test_vertical_alignment`、`test_text_engine_cache`、
  `test_horizontal_whitespace`、`test_vertical_japanese_punctuation`、
  `test_vertical_combined_whitespace`（28 例，3 个既有失败）、
  `test_vertical_roman_alignment`（36 例，7 个既有失败）——与本改动前的基线完全一致，
  无新增失败。

## 上游可提交性

即 `0002`、`0003` 两条记录的结论：两个功能都属「需改造」——通用、默认行为不变、
无新依赖，方向适合上游；提交前需与作者确认 UI 位置、`Auto` 默认值是否合适、
以及与既有 `standard_vertical_roman_alignment` 是否应合并为一个枚举。
`PR.md` 的 "Open questions" 一节已把这些写成具体问题。
