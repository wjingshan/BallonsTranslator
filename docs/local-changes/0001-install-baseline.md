# 0001 安装 v1.5.20 基线并建立 git 记录

- 日期：2026-10-20
- 状态：已验证
- 上游基线：`fa3e137` (tag `v1.5.20`, 2026-10-18)
- 本机路径：`H:\BallonsTranslator`

## 安装前现状

目标目录此前已有一份可运行的安装，但没有版本库：

- `ballontranslator/`：源码 485 个文件
- `ballontrans_pylibs_win/`：内嵌 Python 3.12.10 + 依赖（约 5.2 GB / 32490 文件）
- `data/models/`：4 个模型（comictextdetector.pt 79 MB、comictextdetector.pt.onnx 95 MB、lama_large_512px.ckpt 205 MB、ocr_ar_48px.ckpt 204 MB）
- `input/`：约 869 MB 用户漫画图片
- `config/`：用户配置（10-20 10:31 仍在被写入）
- 无 `.git`，无法追溯任何本地改动

## 本次做的事

1. 克隆上游 `v1.5.20`（浅克隆）用于逐文件比对。
2. 比对结果：580 个受控文件中 572 个 SHA-256 完全一致，**0 个被改动**；另 8 个「缺失」中 2 个是 `git ls-files` 中文路径转义导致的误报（`doc/加别的翻译器.md`、`doc/团子OCR说明.md` 实际存在且字节一致），真正缺的只有 `.github/` 下 6 个文件（release 包不含）。
3. 补回 `.github/`，在目标目录 `git init`，远端指向上游，检出 `v1.5.20` 为 `master` 基线，工作区与上游字节一致。
4. 用 `.git/info/exclude`（而非修改上游 `.gitignore`）排除本地产物：`input/`、`test01/`、`*.zip`、`tmp/`，以及 9 个旧版残留文件（见下）。

## 发现的旧版残留

以下 9 个文件在上游 v1.5.20 中不存在，修改时间为 2026-08-10 ~ 09-17，早于本次安装，判定为更早版本安装的遗留：

| 文件 | 判定 |
| --- | --- |
| `ballontranslator/ui/text_engine/effect_renderer.py` | 死代码。真正被 `item.py:49` 引用的是 `text_engine/effects/renderer.py`（上游自带）。 |
| `ballontranslator/ui/text_engine/rendering/shadow.py` | 仅被上面那个死文件引用。 |
| `resources/translate/es_MX.qm` / `.ts` | 西班牙语翻译，上游无。`utils/shared.py:111` 仍列有 `"Español": "es_MX"`，保留在原地可让西语界面正常工作；删掉会导致该项静默回退。 |
| `resources/icons/icon.icns`、`showpagelist*.svg` | 图标资源，上游无对应项。 |
| `scripts/export to photoshop/Import from BallonTranslator JSON.jsx` | PS 导入脚本，上游该目录结构不同。 |
| `tests/test_llm_translation_context.py` | 旧测试，上游已拆分为 `test_llm_translation_*.py` 系列。 |

处理方式：**不删除、不移走**，仅加入 `.git/info/exclude`，保证 `git status` 干净的同时不损失本地可能用到的资源（尤其西语界面）。

## 验证结果

`git status --porcelain` 为空；`python -m compileall ballontranslator` 通过（唯一警告 `modules/textdetector/panel_finder.py` 的 docstring 转义是上游自带）。

依赖冒烟：

```
APP_VERSION: 1.5.20
qtpy: PyQt6 6.11.0
torch: 2.10.0+cu128 | cuda: True | device: 2
cv2: 5.0.0  numpy: 2.4.6  PIL: 12.3.0
```

注意：验证时已有一个实例在运行（PID 18232，2026-10-20 09:38 启动），未干扰它 —— 后续改动需用户重启该实例才会生效。

## 本机环境注意事项

- 目录所有者是另一个 Windows 账户，Git 报 `dubious ownership`，已加入全局 `safe.directory`。
- 全局 `http.proxy=http://127.0.0.1:7897`，且 schannel 后端报 `SEC_E_NO_CREDENTIALS`，仓库已配置 `http.sslBackend=openssl`，克隆/拉取正常。
- `portable` 性质：`ballontrans_pylibs_win` 是内嵌运行时，不要移动或改名（`launch_win.bat` 依赖该名称）。

## 上游可提交性

不适用 —— 本记录只描述本机安装基线，无代码改动。
