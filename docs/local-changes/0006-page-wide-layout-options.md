# 0006 面板未绑定时，两个排版选项作用于整页

- 日期：2026-10-20
- 状态：已验证（在真实主窗口中端到端验证）
- 相关提交：`feat(ui): apply vertical anchor and Roman rotation to the page when unbound`

## 现象

勾选 `Rotate Roman Words` 后界面显示已勾选，画布上的英文毫无变化，连续多轮如此。

## 排查：三次错误假设，最后靠现场诊断定案

| 假设 | 验证方式 | 结论 |
| --- | --- | --- |
| 旧代码没加载 | 进程启动时间 vs 提交时间、config 里是否出现新字段 | 否，新代码在跑 |
| 竖排列几何缓存没失效 | 真实字体下测 `m` 推进，去掉缓存键变量复测 | 确有该 bug（见 0005），但不是本次现象的原因 |
| 勾选没落到块上 | 读项目 JSON：该页块 `roman_word_rotation` 为 `null` | 成立，但只是现象 |

定案靠一个临时诊断文件（`logs/_layout_diag.txt`，git 忽略），在用户点击那一刻记录现场：

```
manager=SceneTextManager owned=0          ← 当前页文字块列表为空
textLayer=QGraphicsPixmapItem             ← 文字层是位图，无子项
scene_kinds={... 'ControlBlockItem': 8, ...}  ← 只有缩放手柄，没有 TextBlkItem
page_items=0
```

即那次会话里**当前页一个可编辑文字块都没有**，任何格式改动都不可能有可见效果。

同时暴露了我第一版实现的两个真实缺陷：

1. `page_text_items()` 只遍历 `scene.items()` 找 `TextBlkItem`。真实布局里文字块是
   `canvas.textLayer`（`QGraphicsPixmapItem`）的子项、由
   `SceneTextManager.textblk_item_list` 持有；场景遍历未必找得到。
2. 面板残留的绑定块若不属于当前页，会把整页改动吞掉。

## 修复

`page_text_items()` 按可靠性三级取：

1. `SW.st_manager.textblk_item_list`（当前页权威列表，按 idx 顺序）
2. `canvas.textLayer` 的子项
3. 最后才退回场景遍历

`_apply_page_wide_option()` 另外做三件事：

- 绑定的块若不在当前页列表里 → 视为无绑定，退回整页；
- 处于全局模式时同时更新默认值（供以后新建块使用），但只推一条撤销命令；
- 整段用 `try/except` + `LOGGER.exception` 包住：UI 槽里静默失败正是「界面勾上了、
  画布没动」的温床。

## 端到端验证（这次真的在程序里跑）

写了驱动脚本：用 `--proj-dir` 打开用户的 `input/H漫画 同人志/(C91)` 项目，构造
**真实 MainWindow**，在事件循环里执行检查，最后把画布渲染成 PNG 再退出。

- 离屏运行（无字体）确认数据链路：`manager owned=8`、场景 `TextBlkItem=8`；面板在
  **全局模式、未选中块**时执行 `on_param_changed('roman_word_rotation', True)`
  → 目标块 `rot: False → True`、`needs_vertical_rotation('m')=True`。
- 真实字体运行（默认平台）渲染画布并裁切目标气泡：`master` 侧躺紧凑，中文与标点不动。
  这是本功能第一次由真实主窗口证明可用。

## 单元测试

`tests/test_text_layout_page_wide_options.py`（8 例）：

- 整页枚举顺序；
- **场景里没有 TextBlkItem 时仍能从 manager 取到整页**（本次核心回归）；
- 没有 manager 时回退到 `textLayer` 子项；
- 勾选/锚点作用于整页；全局模式同时更新默认值；
- 显式选中不会被扩大；其他参数保持原绑定、不被误扩大。

## 教训（已写进做法）

**在真实主窗口里跑一次，抵过十次离屏推理。** 本轮连续三次「修复」都是先假设、再让用户
验证，代价是用户的时间和信任。以后凡涉及「界面操作 → 画布可见变化」的改动，先用
`--proj-dir` 驱动真实窗口渲染出图，再交给用户确认。

## 上游可提交性

**需改造**：面板语义（默认值 vs 整页）属于产品决策，已作为独立提交放进待发系列，
作者可整条丢弃而不影响前两个功能。
