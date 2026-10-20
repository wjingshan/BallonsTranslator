# 本地改动记录机制

本目录记录本机（fork）对 BallonsTranslator 的所有功能改动。上游仓库没有该目录，因此它不会与上游冲突，也不应出现在提给作者的 PR 中。

## 为什么用两层记录

1. **git commit**：代码事实的唯一权威记录。每个功能改动一个 commit，message 说明「改了什么、为什么、怎么验证」。这是将来导出 patch / 提 PR 的基础。
2. **本目录 Markdown**：面向人的说明。记录需求来源、设计取舍、验证方法、上游可接受性判断。代码 diff 说得清"变了什么"，这里说清"为什么这么变、验证到哪一步"。

## 每个改动的流程

1. 先读 `AGENTS.md` 与相关模块的维护者文档（如 `doc/ui/text_engine.md`）。
2. 改动前确认基线干净：`git status --porcelain` 应为空。
3. 改一处、验证一处；验证方式与结果写进记录。
4. 提交：
   ```bash
   git add -A
   git commit -m "<type>(<scope>): <summary>"
   ```
   message 用英文（将来可能直接提交给作者）。
5. 在本目录新增 `NNNN-<slug>.md`，并在 `INDEX.md` 登记一行。

## 文件命名

- `NNNN-<slug>.md`：序号递增，slug 用英文短横线风格，例如 `0002-escape-clears-focus.md`。
- `INDEX.md`：一行一个改动，含序号、日期、状态（验证中/已验证/待上游）。

## 上游可接受性

每个记录末尾写一段 `## 上游可提交性`，判断该改动是否适合 PR 给 dmMaze：

- **适合**：修复通用 bug、增加通用配置项、不引入新依赖、默认行为不变。
- **需改造**：功能有价值但实现方式偏个人化（硬编码路径、依赖本机环境），提 PR 前需泛化。
- **不适合**：纯个人偏好、依赖本机数据或未公开接口。

## 升级上游版本时

```bash
git fetch origin --tags
git tag -l | tail -3          # 找到新版本号
git rebase v1.5.xx            # 或逐条 cherry-pick
```

本机目录的所有者是另一个 Windows 账户，Windows 上的 Git 需要 `safe.directory` 例外（已写入全局配置）。本机 schannel 后端有认证故障，仓库已配置 `http.sslBackend=openssl`，克隆/拉取均走 openssl。
