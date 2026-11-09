# 0011 分支布局：改版独立成 custom

- 日期：2026-11-09
- 状态：**已验证**
- 上游可提交性：—

## 决定

PR #1376 被上游作者关闭（无评论），此后只在第 1376 号 PR 下留了一条中文留言询问排版部分是否可单独提交，
并明确**不再继续提交**。因此把当前改版固定为独立分支，`master` 交还给上游基线。

```
custom       0b47395  61 提交  日常使用的改版分支（工作区在这里）
master       fa3e137  v1.5.20  跟上游一致，便于 git pull / 后续合并
upstream-pr  7f42576  42 提交  冻结归档：可重放的干净补丁系列
```

`pr-squash`（单提交评审形态）已删除——不再提 PR，它只会增加混乱。

## 为什么这样切

- `master` 保持在 `fa3e137` 后，可以直接 `git fetch origin dev` 并 fast-forward，
  再把上游改动 merge 进 `custom`，不会出现「本地改版挡住上游更新」。
- `custom` 保留全部 61 个提交（含 `docs/local-changes` 记录与 `resources/` 之外的本地内容），
  是唯一需要日常维护的分支。
- `upstream-pr` 不再更新，仅用于按需导出补丁；它的 42 个补丁在
  `H:\DSH\workbench\ball-upstream` 内，可直接 `git am` 重放。

## 同时调整的护栏

`docs/local-changes/verify-upstream-bundle.py` 原来比较 `master` 与 `upstream-pr`。
`master` 回到基线后该比较必然失败，因此新增 `--source` 参数，默认值改为 `custom`：

```bash
python docs/local-changes/verify-upstream-bundle.py
# OK: 42 commit(s), 42 patch(es), full.diff matches, upstream-pr == custom on ...
```

含义变成「补丁包与当前改版分支在 PR 路径上完全一致」，仍然是有效的护栏。

## 日常用法

```bash
# 平时（改版分支）
git checkout custom

# 同步上游
git fetch origin dev
git merge origin/dev            # 在 custom 上合并上游更新

# 只想看上游原版
git checkout master

# 重新导出补丁包（需要时）
git checkout upstream-pr        # 由 custom 的 PR 路径重建后再 format-patch
```

远端目前只有 fork 上的 `vertical-layout-and-canvas-controls`（关闭 PR 的分支）。
若要把改版备份到 fork：`git push myfork custom:custom`（尚未执行，按用户「不用再提交」的要求）。
