"""AI Code Reviewer - 基于本地大模型的 GitHub PR 代码审查工具

用法:
    python main.py https://github.com/owner/repo/pull/123
    python main.py owner/repo#123 --submit
"""
import os
import sys
import argparse
import logging
import yaml

from ollama_client import OllamaClient
from github_client import GitHubClient
from reviewer import CodeReviewer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_config(config_path: str = "") -> dict:
    if not config_path:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def main():
    parser = argparse.ArgumentParser(description="AI Code Reviewer")
    parser.add_argument("pr", help="PR URL 或 owner/repo#number")
    parser.add_argument("--token", help="GitHub Personal Access Token")
    parser.add_argument("--model", help="Ollama 模型名称（默认: qwen2.5-coder:32b）")
    parser.add_argument("--host", default="http://localhost:11434", help="Ollama 服务地址")
    parser.add_argument("--submit", action="store_true", help="自动提交审查结果到 GitHub PR")
    parser.add_argument("--output", "-o", help="将审查报告保存到文件")
    parser.add_argument("--config", "-c", help="配置文件路径")

    args = parser.parse_args()
    config = load_config(args.config)
    model = args.model or config.get("ollama", {}).get("model", "qwen2.5-coder:32b")

    ollama = OllamaClient(
        model=model, host=args.host,
        temperature=config.get("ollama", {}).get("temperature", 0.1),
        max_tokens=config.get("ollama", {}).get("max_tokens", 4096),
    )

    if not ollama.check_available():
        logger.error("Ollama 服务不可用或模型未安装")
        sys.exit(1)

    token = args.token or config.get("github", {}).get("token", "") or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        logger.error("GitHub Token 未设置")
        sys.exit(1)

    github = GitHubClient(token=token)

    import re
    m = re.match(r"(?:https?://github\.com/)?([^/]+)/([^/]+)/(?:pull/)?(\d+)", args.pr)
    if not m:
        m = re.match(r"([^/]+)/([^/]+)#(\d+)", args.pr)
    if not m:
        logger.error(f"无法解析 PR 标识: {args.pr}")
        sys.exit(1)

    owner, repo, pr_number = m.group(1), m.group(2), int(m.group(3))
    logger.info(f"审查 PR: {owner}/{repo}#{pr_number}")

    reviewer = CodeReviewer(
        ollama=ollama, github=github,
        ignore_patterns=config.get("review", {}).get("ignore_patterns", []),
        max_files=config.get("review", {}).get("max_files", 20),
        max_lines=config.get("review", {}).get("max_lines", 500),
    )

    result = reviewer.review_pr(owner, repo, pr_number, submit=args.submit)

    print("\n" + "=" * 60)
    print(result["review_body"])
    print("=" * 60)

    if args.submit:
        print(f"\n审查结果已提交到 PR（{result.get('review_event', 'COMMENT')}）")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["review_body"])
        logger.info(f"审查报告已保存到: {args.output}")

    if any(f["severity"] == "严重" for f in result["findings"]):
        sys.exit(1)


if __name__ == "__main__":
    main()
