# 0014 合并上游 v1.5.22（并恢复 ↵ 自由换行）

- 日期：2026-11-18
- 状态：**已验证**
- 上游可提交性：—

## 上游 v1.5.22 的变化

- 新增 Koharu 检测器 + 自动排版（横竖排沿检测到的气泡形状排布）
- 新增「气泡约束」：字体面板可编辑排版轮廓（锚点/控制柄，双击加锚点）
- **竖排文字新增顶端/居中/底端对齐**（与本地自研功能同名同义）
- 新增 Hayai OCR v2.7 Supernova；删除旧 Hayai、PaddleOCR-VL、ctbd 检测器
- 修复竖排标点位置/旋转、空文本块翻译后塌陷、ezTrans 韩译日
- 数字键 1–0 从「调透明度」改为「激活前 10 个文本样式」

规模：18 提交 / 83 文件 / +9029 −3805；与本地改动重叠 19 文件，试合并冲突 10 文件。

## 合并时用户确认的四项决策

| 决策 | 落地 |
| --- | --- |
| D1 对齐 = 混合 | 单一枚举 `VerticalAlignment`（Auto=-1 保留）；`setVerticalAlignment` 按书写模式分派：竖排走上游墨迹槽位，横排走本地锚点 |
| D2 自由换行 | 当时按「用气泡约束替换」删除 |
| D3 自动字号 | 上游 `fit_text_in_shape` 接管；`manual_font_size` 守卫加在其头部；字号上限扩展到 `apply_pipeline_font_size` |
| D4 行为 | 数字键走上游样式；接受删除 ctbd/旧 Hayai/PaddleOCR-VL；`.qm` 用 lrelease 重编（107561 B） |

## 后续回调：↵ 自由换行已恢复

合并完成后用户确认「自由换行与气泡约束并不冲突」，要求加回 `↵` 手柄。
恢复方式与互斥规则：

| 文件 | 内容 |
| --- | --- |
| `utils/fontformat.py` | 恢复 `no_forced_wrap: bool = False` |
| `utils/textblock.py` | 恢复 `pre_free_wrap_rect` |
| `formatting/commands.py` | 恢复 `push_no_forced_wrap`（走撤销栈、可持久化） |
| `ui/text_engine/editing/manager.py` | 气泡拟合条件加 `and not no_forced_wrap`：**开自由换行时跳过气泡槽位** |
| `vertical_layout.py` | 恢复缓存键项、`available_height = max(…, 1e6)`（优先于 `flow_profile`）、按内容 extent 长高 |
| `horizontal_layout.py` | 恢复 `QTextOption.WrapMode.NoWrap` |
| `ui/text_quick_actions.py` | 恢复 `↵` 手柄、`hug_content`、`restore_original_rect`、`_on_wrap_clicked`；删除重复的 `_snapshot` |
| `tests/test_text_quick_actions.py` | 恢复自由换行相关用例 |

互斥规则：`no_forced_wrap=True` 时忽略气泡轮廓（走 1e6/NoWrap），气泡约束的轮廓编辑照常可用，只是不再约束该块。

## 验证

- `test_text_quick_actions`：22 例通过（含恢复的自由换行用例）
- 关键 8 套件：88 例通过
- `test_bubble_layout` + `test_bubble_editing`：68 例 4 失败，与合并前上游同一批字体度量失败一致，**无新增回归**
- 真机（默认 Qt 平台）：

```
初始      wrap visible=True  checked=False  flag=False  rect 219.0 x 370.0
开自由换行 wrap visible=True  checked=True   flag=True   rect  83.2 x 345.8
关自由换行 wrap visible=True  checked=False  flag=False  rect 219.0 x 370.0
```

## 已知遗留

- 上游 `test_bubble_layout` 4 例、`test_typed_text_effect_renderer` 5 例在本机因字体度量失败，属上游既有
- `vertical_fit.py`（`fit_vertical_font_size`）已无调用，仅测试引用，暂留
- 竖排对齐改用上游墨迹算法后，视觉效果需人工目视验收
