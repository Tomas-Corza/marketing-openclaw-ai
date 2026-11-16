"""Check that all six modular commerce skills are self-contained and correctly linked."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "shopify-product-page-automation": ["tools/shopify_product_pages.py", "docs/shopify-product-page-automation.md"],
    "shopify-bulk-optimization": ["tools/shopify_bulk_feed.py", "docs/shopify-bulk-feed-optimization.md"],
    "shopify-ai-copy-generation": ["tools/shopify_ai_copy.py", "docs/shopify-ai-copy-generation.md"],
    "shopify-product-feed-builder": ["tools/shopify_feed_builder.py", "docs/shopify-product-feed-builder.md"],
    "shopify-feed-sync": ["tools/shopify_live_feed_sync.py", "docs/shopify-live-feed-sync.md"],
    "merchant-feed-diagnostics": ["tools/merchant_feed_diagnostics.py", "docs/merchant-feed-diagnostics.md"],
}


class ModularSkillLayoutTests(unittest.TestCase):
    def test_each_skill_has_valid_unique_frontmatter(self):
        for slug in SKILLS:
            with self.subTest(skill=slug):
                path = ROOT / "skills" / slug / "SKILL.md"
                self.assertTrue(path.is_file(), str(path))
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"))
                self.assertRegex(text, r"(?m)^name: " + re.escape(slug) + r"$")
                self.assertRegex(text, r"(?m)^description: .{20,}$")
                self.assertIn("\n---\n", text)
                self.assertIn("## ", text)

    def test_tool_and_document_references_exist(self):
        for slug, paths in SKILLS.items():
            text = (ROOT / "skills" / slug / "SKILL.md").read_text(encoding="utf-8")
            for ref in paths:
                with self.subTest(skill=slug, path=ref):
                    self.assertTrue((ROOT / ref).is_file(), ref)
                    self.assertIn(ref, text)

    def test_all_skills_listed_in_main_docs(self):
        for doc in ("README.md", "AGENTS.md", "TOOLS.md"):
            content = (ROOT / doc).read_text(encoding="utf-8")
            for slug in SKILLS:
                with self.subTest(document=doc, skill=slug):
                    self.assertIn("skills/" + slug + "/SKILL.md", content)


if __name__ == "__main__":
    unittest.main()
