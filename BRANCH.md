# 分支 `Rae`：个人改版说明

本仓库是 [dmMaze/BallonsTranslator](https://github.com/dmMaze/BallonsTranslator)
的个人修改版，分支 `Rae`。上游项目与版权归原作者所有，许可证仍为 **GPL-3.0**。

分支命名刻意与上游的 `dev` / `master` 区分，避免与官方版本混淆。

## 上游基线

```
v1.5.20 (fa3e137)
```

`master` 保持在该基线上，便于合并上游更新；所有改动集中在 `Rae`。

## 包含的改动

### 竖排排版

- **框内垂直对齐**：文字可在文字框顶部 / 居中 / 底部（新增选项，默认「自动」保持原行为）
- **西文整词旋转**：拉丁单词作为整体压缩进一格，而不是每字母占满一格
- **整词不跨列**：单词放不下时整体移到下一列；超过一列高时按比例压缩（最多 8%），仍放不下则整词放置并让文字框长高
- **自由换行**（文字框旁 `↵` 按钮）：文字不受文字框限制；开启时框自动贴合文字、关闭时恢复到开启前尺寸（含重新打开项目后）

### 批量流水线

- 两个排版选项加入已有的 `let_*` 覆盖机制：批量「运行」时与手动设置结果一致
- 自动字号上限：默认不超过页面中位数的 1.5 倍（0 表示关闭），避免检测框误差导致单个字块异常放大
- 竖排自动放大（可选，默认关闭）：字号偏小时最多放大 1.6 倍填满文字框

### 画布控件

- **原图比对气泡**：按住快捷键或按钮查看原图 / 修复图，松开恢复；快捷键、尺寸、描边均可在设置中调整
- **整页适配放大镜**：一键整页显示（图标变蓝表示处于该状态），翻页保持，再次点击恢复原缩放
- **字号 / 换行手柄**（`T` / `↵`）：`T` 拖拽等比缩放文字与文字框（以框中心为支点，Shift 作用于整页）；`↵` 切换自由换行（Shift 作用于整页）
- 两个手柄的改动都会进入撤销栈，因此可撤销、也会被保存

## 与上游的差异文件

主要集中在这几处：

```
ballontranslator/utils/fontformat.py            新增 vertical_alignment / roman_word_rotation / no_forced_wrap
ballontranslator/ui/text_engine/vertical_layout.py
ballontranslator/ui/text_engine/horizontal_layout.py
ballontranslator/ui/text_engine/layout.py
ballontranslator/ui/text_engine/item.py
ballontranslator/ui/text_engine/pipeline_formatting.py
ballontranslator/ui/text_engine/vertical_fit.py
ballontranslator/ui/layer_peek.py               新增
ballontranslator/ui/page_fit.py                 新增
ballontranslator/ui/text_quick_actions.py       新增
ballontranslator/ui/canvas.py / mainwindow.py / configpanel.py
tests/                                          新增约 105 个测试
```

## 开发记录

`docs/local-changes/` 是本地开发日志（索引见
[docs/local-changes/INDEX.md](docs/local-changes/INDEX.md)），包含每个改动的动机、验证数据与踩坑记录，
不属于上游提交内容。

## 同步上游

```bash
git fetch origin dev
git checkout Rae
git merge origin/dev
```

`master` 未携带本分支改动，因此可以安全地跟上游 fast-forward。

## 说明

- 本分支以自用为目的，未向上游提交（相关 PR 已被作者关闭）
- 图标资源 `resources/icons/layer_peek/*.png` 与 `resources/icons/page_fit/magnifier.svg`
  为本分支自绘；设计源文件 `*.psd` 不入库
- 若上游合并了同类功能，以官方实现为准
