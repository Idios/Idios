import unittest

from scripts.update_readme import build_activity_svg, build_dynamic_section, filter_profile_repositories


class UpdateReadmeTests(unittest.TestCase):
    def test_filters_out_archived_forks_private_and_ignored_repositories(self):
        repos = [
            {"name": "kobutachan-allaganeye", "visibility": "PUBLIC", "isArchived": False, "isFork": False},
            {"name": "automaton", "visibility": "PUBLIC", "isArchived": False, "isFork": False},
            {"name": "private-tool", "visibility": "PRIVATE", "isArchived": False, "isFork": False},
            {"name": "archived-tool", "visibility": "PUBLIC", "isArchived": True, "isFork": False},
            {"name": "forked-tool", "visibility": "PUBLIC", "isArchived": False, "isFork": True},
        ]

        filtered = filter_profile_repositories(repos)

        self.assertEqual([repo["name"] for repo in filtered], ["kobutachan-allaganeye"])

    def test_builds_dynamic_section_with_activity_summary(self):
        repos = [
            {
                "name": "kobutachan-allaganeye",
                "description": "FF14 フロントラインの長時間録画動画を、試合ごとに自動分割するツール。",
                "url": "https://github.com/Idios/kobutachan-allaganeye",
                "visibility": "PUBLIC",
                "isArchived": False,
                "isFork": False,
                "primaryLanguage": {"name": "Python"},
                "pushedAt": "2026-08-31T03:34:08Z",
            },
            {
                "name": "kobutachan-ffxiv-research",
                "description": "",
                "url": "https://github.com/Idios/kobutachan-ffxiv-research",
                "visibility": "PUBLIC",
                "isArchived": False,
                "isFork": False,
                "primaryLanguage": {"name": "Python"},
                "pushedAt": "2026-08-30T15:05:50Z",
            },
            {
                "name": "claudecode-discord-presence",
                "description": "",
                "url": "https://github.com/Idios/claudecode-discord-presence",
                "visibility": "PUBLIC",
                "isArchived": False,
                "isFork": False,
                "primaryLanguage": {"name": "Python"},
                "pushedAt": "2026-07-20T04:27:25Z",
            },
            {
                "name": "automaton",
                "description": "Example Java implementation of finite automaton(state machine).",
                "url": "https://github.com/Idios/automaton",
                "visibility": "PUBLIC",
                "isArchived": False,
                "isFork": False,
                "primaryLanguage": {"name": "Java"},
                "pushedAt": "2012-07-07T15:01:15Z",
            },
        ]

        section = build_dynamic_section(repos, generated_at="2026-08-31 15:45 JST")

        self.assertIn("公開中の表示対象リポジトリ: **3**", section)
        self.assertIn("主な言語: **Python**", section)
        self.assertIn("[kobutachan-allaganeye](https://github.com/Idios/kobutachan-allaganeye)", section)
        self.assertIn("2026-08-31", section)
        self.assertIn("最終更新: 2026-08-31 15:45 JST", section)
        self.assertNotIn("automaton", section)

    def test_builds_activity_svg_without_ignored_repositories(self):
        repos = [
            {
                "name": "kobutachan-allaganeye",
                "visibility": "PUBLIC",
                "isArchived": False,
                "isFork": False,
                "primaryLanguage": {"name": "Python"},
                "pushedAt": "2026-08-31T03:34:08Z",
            },
            {
                "name": "automaton",
                "visibility": "PUBLIC",
                "isArchived": False,
                "isFork": False,
                "primaryLanguage": {"name": "Java"},
                "pushedAt": "2012-07-07T15:01:15Z",
            },
        ]

        svg = build_activity_svg(repos, generated_at="2026-08-31 15:45 JST")

        self.assertIn("<svg", svg)
        self.assertIn("kobutachan-allaganeye", svg)
        self.assertIn("repos: 1", svg)
        self.assertIn("Python", svg)
        self.assertIn("2026-08-31 15:45 JST", svg)
        self.assertNotIn("automaton", svg)


if __name__ == "__main__":
    unittest.main()
