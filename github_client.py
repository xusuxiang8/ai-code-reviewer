"""GitHub API 交互客户端"""
import os
import re
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)
GITHUB_API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str = ""):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        if not self.token:
            raise ValueError("GitHub Token 未设置")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _parse_pr_url(self, pr_url: str) -> tuple[str, str, int]:
        m = re.match(r"(?:https?://github\.com/)?([^/]+)/([^/]+)/pull/(\d+)", pr_url)
        if m:
            return m.group(1), m.group(2), int(m.group(3))
        m = re.match(r"([^/]+)/([^/]+)#(\d+)", pr_url)
        if m:
            return m.group(1), m.group(2), int(m.group(3))
        raise ValueError(f"无法解析 PR 标识: {pr_url}")

    def get_pr_info(self, owner: str, repo: str, pr_number: int) -> dict:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
        resp = self.session.get(url, headers={"Accept": "application/vnd.github.diff"})
        resp.raise_for_status()
        return resp.text

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def submit_review(self, owner: str, repo: str, pr_number: int,
                      body: str, event: str = "COMMENT",
                      comments: Optional[list[dict]] = None) -> dict:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        payload = {"body": body, "event": event}
        if comments:
            payload["comments"] = comments
        resp = self.session.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def add_pr_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        resp = self.session.post(url, json={"body": body})
        resp.raise_for_status()
        return resp.json()
