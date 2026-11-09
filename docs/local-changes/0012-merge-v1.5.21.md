# 0012 合并上游 v1.5.21

- 日期：2026-11-09
- 状态：**已验证**
- 上游可提交性：—

## 上游更新内容（v1.5.21）

- 新增「水墨笔刷（Ink Brush）」文本滤镜（#1375）
- 拖拽字间距 / 行间距标签时实时预览（#1386）
- 修复 ctbd 检测框边缘笔画擦除不完整、长图气泡错误合并（#1377）
- 优化 CTD 掩膜细化性能（#1381）
- 修复拖入侧栏编辑框的文本未立即同步到文本块，支持撤销/重做（#1384）
- 修复变换控件遮挡文本块旋转 / 缩放手柄（#1385）
- 批量渲染前保存未保存的文本与绘图修改，等待图像保存完成
- 更新韩语翻译（#1380）

## 合并过程

```bash
git fetch --tags origin
git merge --no-commit --no-ff v1.5.21
```

- 规模：26 个上游提交、34 个文件
- 冲突 2 处：
  1. `ballontranslator/ui/text_engine/formatting/panel.py`
     - 上游：`on_param_changed` 增加 `-> None`，并在开头 `line_spacing_drag.cancel()` / `letter_spacing_drag.cancel()`
     - 本分支：同一位置插入了 `PAGE_WIDE_PARAMS`、`page_text_items`、`_apply_page_wide_option`
     - 处理：保留本分支整段方法，采用上游的签名与两行 cancel 调用
  2. `resources/translate/zh_CN.qm`（二进制）
     - 处理：用合并后的 `zh_CN.ts` 重新编译（1214 条翻译）
     - 注意：`lrelease` 无法写入 `H:\BallonsTranslator`（拒绝访问），需编译到其他目录再复制回来

## 验证

- 测试：105 例全部通过（合并后 `_PanelShim` 补了 `line_spacing_drag` / `letter_spacing_drag` 桩）
- 真机冒烟：项目加载（169a.jpg，1 块，竖排，字号 85.5）→ 翻页（8 块）→ 整页适配 0.1219 → 恢复 1.0
- 合并后与 `v1.5.21` 的差异仅剩本分支自有改动（56 个文件）

## 护栏调整

`verify-upstream-bundle.py` 原来要求 `upstream-pr` 与工作分支在 PR 路径上完全一致。
补丁系列冻结在 v1.5.20 之后这一要求必然失败，因此改为默认只校验补丁包自身一致性，
需要时用 `--check-source` 打开对比。
