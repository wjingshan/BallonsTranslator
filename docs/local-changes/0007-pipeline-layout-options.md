# 0007 批量「运行」时自动应用两个版面选项

- 日期：2026-10-20
- 状态：已验证（真实主窗口 + 真实「翻译完成」入口）
- 相关提交：`feat(pipeline): apply the layout options during a batch RUN`

## 需求

用户希望点左下角「运行」做批量翻译时，英文自动侧躺，而不是逐页勾 `Rotate Roman Words`。

## 方案：复用流水线已有的「字体格式」覆写机制

流水线在 `MainWindow.on_pagtrans_finished()` 里按属性覆写全局格式，每个属性由一个
`let_*_flag` 控制：`0` = 由程序决定（保留每块自己的值），`1` = 使用全局设置。
这正好对上「一次性设定、以后每页自动」。

新增：

| 位置 | 内容 |
| --- | --- |
| `utils/config.py` | `let_roman_word_rotation_flag`、`let_vertical_alignment_flag`（默认 0） |
| `ui/text_engine/pipeline_formatting.py` | `apply_layout_overrides(blocks, global_format, *, roman_word_rotation, vertical_alignment)` |
| `ui/mainwindow.py` | 读两个 flag；在 `on_pagtrans_finished` 的逐块循环之后调用一次覆写 |
| `ui/configpanel.py` | 「字体格式（流水线）」网格新增两个下拉：`Rotate Roman Words`、`Vertical Align`，选项与既有同类项一致（由程序决定 / 使用全局设置） |

`apply_layout_overrides` 的语义与其它属性一致：flag 为 `1` 时**无条件写入全局值**，
所以它既能把选项打开，也能在全局关掉时把选项关掉；返回发生变化的块数，第二次调用返回 0
（幂等，撤销栈不会被无意义地弄脏）。

## 验证

1. 单元测试 `tests/test_pipeline_layout_overrides.py`（5 例）：flag 关闭不动数据、
   两个 flag 分别复制全局值、flag 开启但全局为关闭时也能关掉、只写被选中的那个选项、
   重复调用返回 0。
2. **真实链路**：驱动真实 `MainWindow` 打开用户的 `(C91)` 项目，设置
   `let_roman_word_rotation_flag = 1`、全局 `roman_word_rotation = True`，
   调用 `on_pagtrans_finished(0)`（即「运行」完成后的那个入口），并**把
   `imgtrans_proj.save` 与 `saveCurrentPage` 打桩为 no-op**，保证不写用户数据：

   ```
   project blocks: 8
   before rot: [False × 8]
   flag = 1 global rot = True
   after rot:  [True × 8]        ← 覆写生效
   scene items: 8 rotated: 8     ← 画布上的活块也更新
   ```

   渲染画布并裁切目标气泡：`master` 侧躺紧凑，中文与标点不动。
   运行后核对项目 JSON 的修改时间仍是 13:43:30（未被本次测试改动）。

## 用户侧怎么用（一次性设定）

重启后：设置 → **字体格式（流水线）** → `Rotate Roman Words` 选「使用全局设置」，
并确保文字面板里全局格式的 `Rotate Roman Words` 是勾上的。之后每次「运行」都会自动带上，
不用再逐页点。

## 上游可提交性

**需改造**：功能通用、默认值不变（flag 默认 0），但新增两个配置项与 UI 行，需要作者认可
命名与放置位置。已作为独立提交放入待发系列。
