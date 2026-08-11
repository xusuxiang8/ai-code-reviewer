# 贡献指南

感谢你考虑为 AI Code Reviewer 做出贡献！

## 如何贡献

### 报告 Bug

在 Issues 中提交 Bug 报告，请包含：
- 操作系统和 Python 版本
- Ollama 版本和使用的模型
- 完整的错误日志
- 复现步骤

### 提交代码

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 提交规范

使用 Conventional Commits：
- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关

## 开发环境

```bash
pip install -r requirements.txt
pip install pytest pytest-cov  # 开发依赖
```

## 添加新审查规则

编辑 `reviewer.py` 中的 `REVIEW_SYSTEM_PROMPT`，添加你想让 AI 关注的新方面。

## 赞助

如果你觉得这个项目有用，欢迎通过 [GitHub Sponsors](https://github.com/sponsors/xusuxiang8) 支持。
