# AI Code Reviewer

基于本地大模型的 GitHub Pull Request 自动代码审查工具。**零 API 费用，完全本地推理。**

使用 [Ollama](https://ollama.com) + [Qwen2.5-Coder](https://ollama.com/library/qwen2.5-coder) 在本地运行，无需任何云端 API 费用。

## 特性

- 完全本地运行 - 代码永远不会离开你的机器
- 零费用 - 无需 OpenAI/Claude API Key
- 智能审查 - 基于 Qwen2.5-Coder 32B 模型
- 结构化报告 - 按严重程度分类：严重 / 警告 / 建议
- GitHub 集成 - 支持自动提交 Review 到 PR
- GitHub Actions - 一键集成到 CI/CD 流水线

## 安装

```bash
git clone https://github.com/xusuxiang8/ai-code-reviewer.git
cd ai-code-reviewer
pip install -r requirements.txt
```

## 使用

```bash
python main.py https://github.com/owner/repo/pull/123 --token ghp_xxx
python main.py https://github.com/owner/repo/pull/123 --token ghp_xxx --submit
python main.py owner/repo#123 --token ghp_xxx --model qwen2.5-coder:7b
python main.py owner/repo#123 --token ghp_xxx -o review.md
```

## 配置

编辑 config.yaml 自定义审查行为，可配置忽略文件模式、最大文件数、审查关注点等。

## 硬件建议

| 模型 | 内存需求 | 推理速度 |
|------|---------|---------|
| qwen2.5-coder:32b | 20GB+ | 较慢但质量高 |
| qwen2.5-coder:7b | 6GB+ | 快速 |

## License

MIT License
