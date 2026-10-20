# 0010 上传前的整理与勾选清单

- 日期：2026-10-20
- 状态：**待用户上传**（代码已就绪，推送需要用户自己的 fork）

## 当前仓库状态

```
分支      master      2d8da1c   （50 个提交，含本地记录与工具）
          upstream-pr 33 个提交（仅 ballontranslator/ doc/ tests/）
          pr-squash   1 个提交（同 upstream-pr 的树，便于单提交评审）
工作区    干净
远端      origin = https://github.com/dmMaze/BallonsTranslator.git  ← 上游，不是 fork
```

**重要**：`origin` 指向官方仓库。不要 `git push origin master`：既无权限，也不该往
上游主干推。上传前必须先有用户自己的 fork。

## 上传步骤（需要用户执行或授权）

```bash
# 1. 在 GitHub 上 fork dmMaze/BallonsTranslator，然后：
cd H:\BallonsTranslator
git remote add myfork https://github.com/wjingshan/BallonsTranslator.git   # 已创建并推送

# 2a. 想按 33 个提交评审：
git push myfork upstream-pr:vertical-layout-and-canvas-controls

# 2b. 想按单提交评审（与 2a 二选一）：
git push myfork pr-squash:vertical-layout-and-canvas-controls

# 3. 在 GitHub 上以 vertical-layout-and-canvas-controls → dmMaze:master 开 PR，
#    正文使用 H:\DSH\workbench\ball-upstream\PR.md
```

`docs/local-changes/` 与 `resources/icons/layer_peek`、`resources/icons/page_fit` 不在补丁
路径内，不会进入 PR；这是有意的（前者是开发记录，后者是 fork 的美术资源）。

## 上传前勾选清单

- [x] `git status` 干净
- [x] `python docs/local-changes/verify-upstream-bundle.py` 绿灯（33 提交 / 33 补丁 /
      `full.diff` 一致）
- [x] pristine v1.5.20 上 `git am` 逐个补丁重放无冲突、与分支零差异
- [x] 96 个新测试通过；既有失败项（竖排对齐 7 个、空白/标点 3 个）与本分支无关且数量不变
- [x] 真机验证记录见 `PR.md` 的表格（探图、整页适配、自由换行、缩放支点、Shift 整页）
- [x] `PR.md` 已按最终形态重写（功能分组、行为说明、验证数据、待决问题）
- [ ] 用户 fork 已创建并配置 `myfork` 远端
- [x] 已推送 33 提交形态：分支 ertical-layout-and-canvas-controls
- [ ] 开 PR 并粘贴 `PR.md` 正文

## 上传后建议

1. 若作者只想要排版改动：前两组提交（垂直对齐、整词旋转）可独立成 PR，后续
   UI 控件可按需拆分。
2. 若作者要求英文注释统一：当前代码注释为英文，界面文案走 `.ts` 词表，无需调整。
3. 若作者要求 changelog：把 `PR.md` 的「Verification」表整理成一段即可。
