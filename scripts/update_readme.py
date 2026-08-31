from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


USERNAME = "Idios"
IGNORE_REPOSITORIES = {"Idios", "automaton"}
START_MARKER = "<!-- ACTIVITY:START -->"
END_MARKER = "<!-- ACTIVITY:END -->"


def filter_profile_repositories(repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        repo
        for repo in repositories
        if repo.get("visibility") == "PUBLIC"
        and not repo.get("isArchived")
        and not repo.get("isFork")
        and repo.get("name") not in IGNORE_REPOSITORIES
    ]


def _repo_pushed_at(repository: dict[str, Any]) -> str:
    return repository.get("pushedAt") or repository.get("updatedAt") or ""


def _format_date(value: str) -> str:
    if not value:
        return "更新日不明"
    return value[:10]


def _language_name(repository: dict[str, Any]) -> str | None:
    language = repository.get("primaryLanguage")
    if isinstance(language, dict):
        return language.get("name")
    if isinstance(language, str):
        return language
    return None


def build_dynamic_section(repositories: list[dict[str, Any]], generated_at: str | None = None) -> str:
    visible_repos = sorted(
        filter_profile_repositories(repositories),
        key=_repo_pushed_at,
        reverse=True,
    )
    language_counts = Counter(
        language for repository in visible_repos if (language := _language_name(repository))
    )
    language_summary = "、".join(language for language, _ in language_counts.most_common(5)) or "集計なし"
    generated_at = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows = [
        "| リポジトリ | 内容 | 最終更新 |",
        "| --- | --- | --- |",
    ]
    for repository in visible_repos[:6]:
        name = repository["name"]
        description = repository.get("description") or "説明を準備中"
        url = repository.get("url") or f"https://github.com/{USERNAME}/{name}"
        rows.append(f"| [{name}]({url}) | {description} | {_format_date(_repo_pushed_at(repository))} |")

    return "\n".join(
        [
            f"- 公開中の表示対象リポジトリ: **{len(visible_repos)}**",
            f"- 主な言語: **{language_summary}**",
            f"- 最終更新: {generated_at}",
            "",
            *rows,
        ]
    )


def build_activity_svg(repositories: list[dict[str, Any]], generated_at: str | None = None) -> str:
    visible_repos = sorted(
        filter_profile_repositories(repositories),
        key=_repo_pushed_at,
        reverse=True,
    )
    language_counts = Counter(
        language for repository in visible_repos if (language := _language_name(repository))
    )
    language_summary = " / ".join(language for language, _ in language_counts.most_common(3)) or "no data"
    latest_repo = visible_repos[0]["name"] if visible_repos else "no public repo"
    latest_date = _format_date(_repo_pushed_at(visible_repos[0])) if visible_repos else "no update"
    generated_at = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<svg width="860" height="230" viewBox="0 0 860 230" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Idios activity summary</title>
  <desc id="desc">GitHub activity summary generated from public repositories.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="860" y2="230" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#101828"/>
      <stop offset="0.55" stop-color="#123D5A"/>
      <stop offset="1" stop-color="#22543D"/>
    </linearGradient>
    <linearGradient id="line" x1="40" y1="176" x2="820" y2="176" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#7DD3FC"/>
      <stop offset="0.5" stop-color="#A7F3D0"/>
      <stop offset="1" stop-color="#FDE68A"/>
    </linearGradient>
  </defs>
  <rect width="860" height="230" rx="18" fill="url(#bg)"/>
  <path d="M48 176 C168 120 238 202 356 150 S548 128 646 88 S760 82 812 48" stroke="url(#line)" stroke-width="4" stroke-linecap="round"/>
  <circle cx="646" cy="88" r="7" fill="#A7F3D0"/>
  <circle cx="812" cy="48" r="7" fill="#FDE68A"/>
  <text x="40" y="58" fill="#FFFFFF" font-family="Segoe UI, Arial, sans-serif" font-size="32" font-weight="700">Idios</text>
  <text x="40" y="91" fill="#D1E9FF" font-family="Segoe UI, Arial, sans-serif" font-size="16">local-first tools / media workflow / practical packaging</text>
  <text x="40" y="138" fill="#FFFFFF" font-family="Segoe UI, Arial, sans-serif" font-size="24" font-weight="700">repos: {len(visible_repos)}</text>
  <text x="185" y="138" fill="#FFFFFF" font-family="Segoe UI, Arial, sans-serif" font-size="24" font-weight="700">{html.escape(language_summary)}</text>
  <text x="40" y="204" fill="#E0F2FE" font-family="Segoe UI, Arial, sans-serif" font-size="14">latest: {html.escape(latest_repo)} / {latest_date}</text>
  <text x="620" y="204" fill="#C7D2FE" font-family="Segoe UI, Arial, sans-serif" font-size="13">updated: {html.escape(generated_at)}</text>
</svg>
"""


def replace_dynamic_section(readme: str, section: str) -> str:
    start = readme.index(START_MARKER) + len(START_MARKER)
    end = readme.index(END_MARKER)
    return f"{readme[:start]}\n{section}\n{readme[end:]}"


def fetch_repositories_with_gh() -> list[dict[str, Any]]:
    command = [
        "gh",
        "repo",
        "list",
        USERNAME,
        "--limit",
        "100",
        "--json",
        "name,description,visibility,isArchived,isFork,primaryLanguage,pushedAt,updatedAt,url",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(completed.stdout)


def fetch_repositories_with_api() -> list[dict[str, Any]]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "IdiosProfileReadme",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=pushed",
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)

    return [
        {
            "name": repo.get("name"),
            "description": repo.get("description") or "",
            "visibility": "PUBLIC" if not repo.get("private") else "PRIVATE",
            "isArchived": repo.get("archived", False),
            "isFork": repo.get("fork", False),
            "primaryLanguage": {"name": repo.get("language")} if repo.get("language") else None,
            "pushedAt": repo.get("pushed_at"),
            "updatedAt": repo.get("updated_at"),
            "url": repo.get("html_url"),
        }
        for repo in data
    ]


def fetch_repositories() -> list[dict[str, Any]]:
    try:
        return fetch_repositories_with_gh()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return fetch_repositories_with_api()


def update_readme(readme_path: Path) -> None:
    repositories = fetch_repositories()
    section = build_dynamic_section(repositories)
    assets_dir = readme_path.parent / "assets"
    assets_dir.mkdir(exist_ok=True)
    (assets_dir / "activity.svg").write_text(build_activity_svg(repositories), encoding="utf-8", newline="\n")
    readme = readme_path.read_text(encoding="utf-8")
    readme_path.write_text(replace_dynamic_section(readme, section), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update the dynamic activity section in README.md.")
    parser.add_argument("--readme", default="README.md", type=Path)
    args = parser.parse_args()

    try:
        update_readme(args.readme)
    except ValueError as exc:
        print(f"README markers are missing: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
