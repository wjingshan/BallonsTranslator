# 0005 修复：勾选整词旋转后竖排几何不更新

- 日期：2026-10-20
- 状态：已验证
- 相关提交：`fix(text): invalidate the vertical column cache when Roman rotation changes`

## 现象

用户在「进阶字体格式」面板勾选了 `Rotate Roman Words`，画布上的英文仍是
「一格一字母、字母正立」，与勾选前完全相同。

## 排查过程（先分清「没作用到块」还是「作用了但几何没重建」）

1. 确认程序确实是新代码：用户实例 PID 25124 启动于 13:05，晚于功能提交时间
   11:35；且 `config.json` 里已经出现新增字段 `roman_word_rotation`。
2. 放大用户截图：字母是**正立**的，说明是「旋转分支未生效」，而不是旋转了但不够紧凑。
3. 用真实字体做对照实验，测 `m` 的竖向推进：

   | 场景 | m 推进 |
   | --- | --- |
   | 新建时关闭 | 33.22 |
   | 新建时开启 | 32.44（正确） |
   | 实时勾选后 | 33.22（错误，与关闭相同） |
   | 命令路径 | 33.22（错误） |
   | 反复 `reLayout()` | 33.22（错误，不是一次性抖动） |

4. 结论：**新建时正确、切换时错误**，指向缓存而不是排版算法本身。

## 根因

`VerticalTextDocumentLayout` 有一层「整列几何缓存」（`_plain_column_cache` /
`_plain_column_reused`），其失效键是 `_plain_column_context` 元组，里面列了
`standard_vertical_roman_alignment`、`letter_spacing`、`available_height` 等
影响列几何的输入——但我新加的 `roman_word_rotation` **没有列进去**。

于是：新建时缓存为空，按新标志测出紧凑几何；勾选时键没变，缓存被判定有效，
`_reuse_plain_column()` 把「正立、每字一个 em 格」的旧几何原样重放。

真实字体下的实测缓存状态：

```
after relayout    : plain_cache=1 reused={0}   ← 正在复用旧几何
after toggle      : plain_cache=1 reused=set() ← 换成修复后：键变了，缓存被清
```

## 修复

把 `self.fontformat.roman_word_rotation` 加入 `_plain_column_context`
（`vertical_layout.py`，紧跟 `standard_vertical_roman_alignment`）。

修复后：实时勾选 → 32.44，与新建时开启完全一致；命令路径一致；重复重排保持。

## 回归测试

`tests/test_text_roman_word_rotation.py::test_column_cache_key_separates_both_rotation_values`

断言「两种旋转取值必须产生不同的缓存键」，而不是断言像素推进量。原因：本机离屏
测试平台**没有任何字体**（所有字形按 em 方块测量），两种取值的推进在离屏下相同，
断言推进量无法区分；而缓存键是否区分则是字体无关的确定事实。

已验证该测试在**去掉修复后失败**（`FAILED (failures=1)`），加回修复后通过。

## 验证

- 两个新套件共 **31 例通过**。
- 既有关联套件：5 套 28 例（3 个既有失败）、`test_vertical_roman_alignment` 36 例
  （7 个既有失败）——与本改动前基线完全一致，无新增失败。
- 真实字体渲染对比：勾选后 `master` 变为紧凑侧躺（节省约 20% 纵向空间），中文与
  标点不变。

## 顺带发现（未修，属上游既有行为）

面板在**没有选中文字块**时改动任一格式参数会抛
`AttributeError: 'NoneType' object has no attribute 'fontformat'`：
`wrap_fntformat_input(values, None, False)` 会得到 `blkitems=[None]`。
这个缺陷对**所有**参数都一样（`ffmt_change_alignment` 等同样如此），不是本次新增，
但表现是「界面勾上了、画布没反应」。修法是在 `on_param_changed` 的非全局分支里
先判断是否有目标；因涉及上游公共路径，留作单独改动。

## 上游可提交性

**适合**：这是 0003 功能的缺陷修复，改动一行 + 一条测试，默认行为不变。
若 0003 以系列形式提交，本修复应折进 0003 的提交（已按此重建 `upstream-pr`）。
