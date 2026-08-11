"""核心审查引擎"""
import re
import json
import logging
from typing import Optional
from ollama_client import OllamaClient
from github_client import GitHubClient

logger = logging.getLogger(__name__)

REVIEW_SYSTEM_PROMPT = """你是一位资深代码审查专家。你会收到一个 Pull Request 的代码变更(diff)。

请仔细审查代码，关注以下方面：
1. 安全漏洞（SQL注入、XSS、敏感信息泄露、不安全的反序列化等）
2. 逻辑错误和潜在 Bug
3. 性能问题和资源泄漏（内存泄漏、数据库连接未关闭等）
4. 错误处理是否完善
5. 边界情况和空值处理
6. 代码可读性和可维护性

审查规则：
- 只对真正有问题的地方提出建议
- 每条建议给出严重程度：严重 / 警告 / 建议
- 明确指出问题所在的具体代码行
- 给出具体的修改建议
- 如果没有发现问题，只需回复"未发现明显问题"
- 使用中文回复

请按以下 JSON 格式输出审查结果（仅输出 JSON）：
{
  "summary": "一句话总结",
  "findings": [
    {
      "severity": "严重 / 警告 / 建议",
      "file": "文件路径",
      "line": "行号",
      "title": "问题标题",
      "description": "详细描述",
      "suggestion": "修改建议"
    }
  ]
}"""


class CodeReviewer:
    def __init__(self, ollama: OllamaClient, github: GitHubClient,
                 ignore_patterns: Optional[list[str]] = None,
                 max_files: int = 20, max_lines: int = 500):
        self.ollama = ollama
        self.github = github
        self.ignore_patterns = ignore_patterns or []
        self.max_files = max_files
        self.max_lines = max_lines

    def _should_ignore(self, filename: str) -> bool:
        import fnmatch
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(filename.split("/")[-1], pattern):
                return True
        return False

    def _split_diff_by_file(self, diff_text: str) -> list:
        files = []
        current_file = None
        current_lines = []
        for line in diff_text.split("\n"):
            m = re.match(r"^diff --git a/(.+) b/(.+)$", line)
            if m:
                if current_file and current_lines:
                    files.append((current_file, "\n".join(current_lines)))
                current_file = m.group(2)
                current_lines = [line]
            elif current_file:
                current_lines.append(line)
        if current_file and current_lines:
            files.append((current_file, "\n".join(current_lines)))
        return files

    def _parse_review_json(self, response: str) -> dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        m = re.search(r"\{[\s\S]*\"findings\"[\s\S]*\}", response)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return {"summary": response, "findings": []}

    def review_file(self, filename: str, file_diff: str) -> dict:
        lines = file_diff.split("\n")
        if len(lines) > self.max_lines + 50:
            file_diff = "\n".join(lines[:self.max_lines + 50])
            file_diff += f"\n\n... (文件过长，已截断，共 {len(lines)} 行)"
        prompt = f"""请审查以下文件的代码变更：

文件：{filename}

```diff
{file_diff}
```"""
        try:
            response = self.ollama.generate(prompt=prompt, system=REVIEW_SYSTEM_PROMPT)
            result = self._parse_review_json(response)
            result["_file"] = filename
            return result
        except Exception as e:
            logger.error(f"审查文件 {filename} 失败: {e}")
            return {"summary": f"审查失败: {e}", "findings": [], "_file": filename}

    def review_pr(self, owner: str, repo: str, pr_number: int, submit: bool = False) -> dict:
        pr_info = self.github.get_pr_info(owner, repo, pr_number)
        pr_title = pr_info.get("title", "")
        diff_text = self.github.get_pr_diff(owner, repo, pr_number)
        file_diffs = self._split_diff_by_file(diff_text)

        filtered, skipped = [], []
        for filename, fdiff in file_diffs:
            if self._should_ignore(filename):
                skipped.append(filename)
                continue
            if len(fdiff.split("\n")) > self.max_lines * 2:
                skipped.append(f"{filename} (行数过多)")
                continue
            filtered.append((filename, fdiff))

        if len(filtered) > self.max_files:
            skipped.extend(f[0] for f in filtered[self.max_files:])
            filtered = filtered[:self.max_files]

        all_findings = []
        for filename, fdiff in filtered:
            logger.info(f"审查: {filename}")
            result = self.review_file(filename, fdiff)
            for f in result.get("findings", []):
                f["file"] = f.get("file", filename)
            all_findings.extend(result.get("findings", []))

        severity_order = {"严重": 0, "警告": 1, "建议": 2}
        all_findings.sort(key=lambda x: severity_order.get(x.get("severity", ""), 99))
        review_body = self._build_review_body(pr_title, all_findings, skipped)

        result = {
            "owner": owner, "repo": repo, "pr_number": pr_number,
            "pr_title": pr_title, "files_reviewed": len(filtered),
            "files_skipped": skipped, "findings": all_findings,
            "review_body": review_body,
        }

        if submit and all_findings:
            event = "REQUEST_CHANGES" if any(f["severity"] == "严重" for f in all_findings) else "COMMENT"
            self.github.submit_review(owner, repo, pr_number, body=review_body, event=event)
            result["submitted"] = True
            result["review_event"] = event
        return result

    def _build_review_body(self, pr_title: str, findings: list, skipped: list) -> str:
        lines = [
            "## AI 代码审查报告", "",
            f"**PR**: {pr_title}",
            f"**审查模型**: {self.ollama.model}",
            f"**发现问题**: {len(findings)} 个", "", "---",
        ]
        if not findings:
            lines.append("\n未发现明显问题，代码质量良好。\n")
        else:
            severity_groups = {"严重": [], "警告": [], "建议": []}
            for f in findings:
                severity_groups[f.get("severity", "建议")].append(f)
            for sev_label, sev_findings in severity_groups.items():
                if not sev_findings:
                    continue
                lines.append(f"\n### {sev_label}（{len(sev_findings)} 个）\n")
                for i, f in enumerate(sev_findings, 1):
                    lines.append(f"#### {i}. {f.get('title', '未命名')}")
                    lines.append(f"- 文件: `{f.get('file', '')}`")
                    lines.append(f"- 位置: 第 {f.get('line', 'N/A')} 行")
                    lines.append(f"- 描述: {f.get('description', '')}")
                    suggestion = f.get("suggestion", "")
                    if suggestion:
                        lines.append(f"- 建议:\n```\n{suggestion}\n```")
                    lines.append("")
        if skipped:
            lines.append("---")
            lines.append(f"\n### 跳过的文件（{len(skipped)} 个）\n")
            for s in skipped:
                lines.append(f"- `{s}`")
        lines.append("\n---")
        lines.append("\n*本审查由 AI Code Reviewer 自动生成，仅供参考。请人工复核。*")
        return "\n".join(lines)
