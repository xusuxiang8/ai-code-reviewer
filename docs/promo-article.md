# 我用 64GB 内存跑了一个本地大模型，免费给 GitHub PR 做代码审查

## 为什么要做这个

市面上的 AI 代码审查工具很多——CodeRabbit、ReviewPad、Copilot——但它们都有一个共同点：**你的代码要上传到别人的服务器**。

我不喜欢这样。代码是一个开发者的核心资产，为什么要交给第三方？更别说那些工具还要收费。CodeRabbit 每月 $12 起步。

## 我的方案：零 API 费用 + 完全本地

我的电脑配置不算顶配：AMD RYZEN AI MAX+ 395，64GB 内存，4GB 显存。但这足够跑 Qwen2.5-Coder 32B 了。

于是我做了一个开源工具：**AI Code Reviewer**。

工作流程很简单：
1. 你给它一个 GitHub PR 链接
2. 它拉取代码 diff
3. 把 diff 发给本地 Ollama 运行的 Qwen2.5-Coder
4. 模型逐个文件审查，生成报告
5. 自动提交 Review 评论到 PR

全程代码不离开你的电脑，零 API 费用。

## 实际效果

审查范围包括：安全漏洞、逻辑错误、性能问题、错误处理、代码可读性。报告按严重程度分级，直接贴在 PR 评论区。

## 快速开始

```bash
ollama pull qwen2.5-coder:32b
git clone https://github.com/xusuxiang8/ai-code-reviewer.git
cd ai-code-reviewer
pip install -r requirements.txt
python main.py owner/repo#123 --token ghp_xxx --submit
```

## 硬件需求

| 模型 | 内存 | 适合 |
|------|------|------|
| qwen2.5-coder:32b | 20GB+ | 高质量审查 |
| qwen2.5-coder:7b | 6GB+ | 快速响应 |

如果觉得有用，欢迎 Star 和 Sponsors 支持。
