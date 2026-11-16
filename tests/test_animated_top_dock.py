"""
Test Suite: Exact ThreeUI AnimatedTopDock Component Integration Verification
Validates:
1. Exact source retrieval & SHA-256 hash match for all 5 source files + font asset.
2. Source revision match: 5a736cd3c1f6f19802f61ebb10e1701b9f7aa26e.
3. @designcodeio/threeui package and styles integration.
4. Exact component configuration & props in BottomRightDock:
   variant="modern", proximity={138}, spring={0.19}, damping={0.70}, widthGrowth={17}, heightGrowth={16}, drop={3.5}
   inside .shader-frame container.
5. HeaderNav layout:
   - LEFT: NOVANEST wordmark & END - TO - END BUSINESS ANALYTICS SYSTEM, DECISION SUITE 2.0
   - RIGHT: Territory selector, Live IST clock, Data pipeline status, Core engine status, Theme switcher
   - Top navbar: AnimatedTopDock removed from header to prevent duplicates.
6. Navigation mapping connecting dock buttons to NovaNest tab destinations.
7. Positioning at bottom-right viewport without overlapping floating chatbot.
8. Preservation of existing dashboard intelligence routes, floating chatbot, themes, and backend APIs.
"""

import hashlib
import json
import re
import unittest
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_HASHES = {
    "src/shaders/animated-top-dock/AnimatedTopDock.tsx": "50ddbba7ebc81565f42bd14dda34efb45e7b18c1aa47e97f196256ffedb4478f",
    "src/shaders/animated-top-dock/topDockController.ts": "506ab23d4d42cf1b5bc89131e7714586ee107381bb18d9b0302766e9a1dee2bd",
    "src/shaders/animated-top-dock/retroPixelField.ts": "54f0469be51dfce2da7ce37c952d42c583cc7996794bf96d1ea0b2bb35d94115",
    "src/shaders/animated-top-dock/glassParticleField.ts": "bc9f07ae6da33b28f82303ea937095806f8e3a2ab08bd1301ae8457aaf0c3464",
    "src/shaders/threeui.css": "efe4447139f1358dd8e9be68edf6fa46cbefbd1de423a4d6c439ca61d2c8eccf",
    "src/shaders/fonts/fragment-mono.woff2": "4f4dc27f4a770c0d02fde800daa836c8adc0d1e423b28da74baaf0d1cc3ab96c",
}

EXPECTED_REVISION = "5a736cd3c1f6f19802f61ebb10e1701b9f7aa26e"


class TestAnimatedTopDockIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend_dir = PROJECT_ROOT / "frontend"
        cls.header_path = cls.frontend_dir / "src" / "components" / "HeaderNav.tsx"
        cls.dock_path = cls.frontend_dir / "src" / "components" / "BottomRightDock.tsx"
        cls.chatbot_path = cls.frontend_dir / "src" / "components" / "FloatingChatbot.tsx"
        cls.app_path = cls.frontend_dir / "src" / "App.tsx"
        cls.index_css_path = cls.frontend_dir / "src" / "index.css"
        cls.package_json_path = cls.frontend_dir / "package.json"
        cls.api_base = "http://127.0.0.1:8000"

    def test_01_source_revision_verification(self):
        """Verify the registered source bundle matches revision 5a736cd3c1f6f19802f61ebb10e1701b9f7aa26e."""
        bundle_resp = requests.get("https://threeui.com/source-code/animated-top-dock.json", timeout=10)
        self.assertEqual(bundle_resp.status_code, 200, "Source bundle endpoint must return HTTP 200")
        bundle_data = bundle_resp.json()
        self.assertEqual(bundle_data.get("id"), "animated-top-dock")
        self.assertEqual(bundle_data.get("schemaVersion"), 1)

        # Check revision commit in ThreeUI upstream registry
        site_html = requests.get("https://threeui.com", timeout=10).text
        match = re.search(r'src=["\'](/assets/index-[^"\']+\.js)["\']', site_html)
        js_url = f"https://threeui.com{match.group(1)}" if match else "https://threeui.com/assets/index-Cf3aCPch.js"
        site_js = requests.get(js_url, timeout=10).text
        self.assertIn(
            EXPECTED_REVISION,
            site_js,
            f"Expected commit revision {EXPECTED_REVISION} must be present in threeui.com release bundle",
        )

    def test_02_source_files_and_font_sha256_hashes(self):
        """Verify all 5 source files and the binary font asset match their exact SHA-256 hashes."""
        for rel_path, expected_hash in EXPECTED_HASHES.items():
            file_path = self.frontend_dir / rel_path
            self.assertTrue(file_path.exists(), f"File {rel_path} must exist on disk at {file_path}")
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            self.assertEqual(
                actual_hash,
                expected_hash,
                f"Hash mismatch for {rel_path}: actual={actual_hash}, expected={expected_hash}",
            )

    def test_03_package_installation_and_imports(self):
        """Verify @designcodeio/threeui is installed and imported cleanly in BottomRightDock."""
        pkg = json.loads(self.package_json_path.read_text(encoding="utf-8"))
        deps = pkg.get("dependencies", {})
        self.assertIn("@designcodeio/threeui", deps, "@designcodeio/threeui must be in package.json dependencies")
        self.assertIn("three", deps, "three peer dependency must be installed in package.json")

        self.assertTrue(self.dock_path.exists(), "BottomRightDock.tsx component must exist")
        dock_content = self.dock_path.read_text(encoding="utf-8")
        self.assertIn(
            'import { AnimatedTopDock } from "@designcodeio/threeui";',
            dock_content,
            "BottomRightDock must use exact documented import: import { AnimatedTopDock } from '@designcodeio/threeui';",
        )
        self.assertIn(
            'import "@designcodeio/threeui/style.css";',
            dock_content,
            "BottomRightDock must use exact documented import: import '@designcodeio/threeui/style.css';",
        )

    def test_04_exact_component_props_and_shader_frame(self):
        """Verify AnimatedTopDock is rendered inside shader-frame with the exact configuration."""
        content = self.dock_path.read_text(encoding="utf-8")
        self.assertIn("shader-frame", content, "AnimatedTopDock must be rendered inside shader-frame container")

        expected_props = [
            'variant="modern"',
            "proximity={138}",
            "spring={0.19}",
            "damping={0.70}",
            "widthGrowth={17}",
            "heightGrowth={16}",
            "drop={3.5}",
        ]
        for prop in expected_props:
            self.assertIn(prop, content, f"BottomRightDock must pass exact prop: {prop}")

    def test_05_header_nav_branding_and_controls_without_dock(self):
        """Verify HeaderNav maintains Left branding and Right controls, and dock is removed from navbar."""
        content = self.header_path.read_text(encoding="utf-8")

        # LEFT
        self.assertIn("NOVANEST", content, "Left zone must include NOVANEST wordmark")
        self.assertIn("END - TO - END BUSINESS ANALYTICS SYSTEM", content, "Left zone must include subtitle")
        self.assertIn("DECISION SUITE 2.0", content, "Left zone must include DECISION SUITE 2.0 badge")

        # Top navbar does NOT contain AnimatedTopDock (removed to prevent duplicates)
        self.assertNotIn("<AnimatedTopDock", content, "Top navbar must not contain AnimatedTopDock")

        # RIGHT
        self.assertIn("MapPin", content, "Right zone must include territory icon")
        self.assertIn("selectedCity", content, "Right zone must include city selector")
        self.assertIn("Data Pipeline:", content, "Right zone must include data pipeline badge")
        self.assertIn("Clock", content, "Right zone must include clock icon")
        self.assertIn("Core Engine Online", content, "Right zone must include core engine status")
        self.assertIn("<ThemeSwitcher />", content, "Right zone must include ThemeSwitcher")

    def test_06_navigation_event_mapping(self):
        """Verify dock buttons connect to NovaNest tab destinations without modifying verified source."""
        content = self.dock_path.read_text(encoding="utf-8")
        self.assertIn("handleDockClick", content, "BottomRightDock must implement handleDockClick event delegation")
        self.assertIn("onTabChange", content, "BottomRightDock must pass tab transitions via onTabChange")
        self.assertIn("'overview'", content, "Product item must route to overview")
        self.assertIn("'decision'", content, "Solutions item must route to decision")
        self.assertIn("'command_center'", content, "Docs item must route to command_center")
        self.assertIn("'financial'", content, "Pricing item must route to financial")
        self.assertIn("'operations'", content, "Changelog item must route to operations")

    def test_07_css_shader_frame_and_font_definitions(self):
        """Verify CSS contains .shader-frame rules, Fragment Mono font-face, and theme adaptations."""
        css_content = self.index_css_path.read_text(encoding="utf-8")
        self.assertIn(".shader-frame", css_content, "index.css must define .shader-frame")
        self.assertIn("Fragment Mono", css_content, "index.css must define Fragment Mono font-face")
        self.assertIn("atd-modern", css_content, "index.css must style atd-modern container")
        self.assertIn('[data-theme="light"]', css_content, "index.css must include light theme adaptation for dock")

    def test_08_preservation_of_existing_features(self):
        """Verify existing features (8 sidebar tabs, floating chatbot, themes, backend APIs) remain untouched."""
        # Check Sidebar
        sidebar_content = (self.frontend_dir / "src" / "components" / "Sidebar.tsx").read_text(encoding="utf-8")
        for key in ["overview", "customer", "restaurant", "operations", "financial", "decision", "simulator", "command_center"]:
            self.assertIn(f"key: '{key}'", sidebar_content, f"Sidebar must preserve key '{key}'")

        # Check App.tsx has FloatingChatbot and BottomRightDock
        app_content = self.app_path.read_text(encoding="utf-8")
        self.assertIn("<FloatingChatbot />", app_content, "App.tsx must preserve FloatingChatbot")
        self.assertIn("<BottomRightDock", app_content, "App.tsx must render BottomRightDock")

        # Check backend health
        try:
            health_resp = requests.get(f"{self.api_base}/api/health", timeout=5)
            self.assertEqual(health_resp.status_code, 200, "Backend /api/health must be 200")
            health_json = health_resp.json()
            self.assertEqual(health_json.get("status"), "healthy")
        except Exception as e:
            self.fail(f"Backend API health check failed: {e}")

    def test_09_bottom_right_positioning_and_no_overlap(self):
        """Verify bottom-right dock positioning and that it does not collide with floating chatbot."""
        dock_content = self.dock_path.read_text(encoding="utf-8")
        chatbot_content = self.chatbot_path.read_text(encoding="utf-8")

        self.assertIn("fixed", dock_content, "BottomRightDock must have fixed positioning")
        self.assertIn("right-", dock_content, "BottomRightDock must be aligned to right")
        self.assertIn("bottom-", dock_content, "BottomRightDock must be aligned to bottom")

        # Check that chatbot launcher is at bottom-6 and dock is at bottom-22/24 (stacked cleanly)
        self.assertIn("bottom-6", chatbot_content, "Chatbot must be at bottom-6")
        self.assertTrue(
            "bottom-22" in dock_content or "bottom-24" in dock_content,
            "BottomRightDock must be positioned with bottom offset above chatbot launcher",
        )


if __name__ == "__main__":
    unittest.main()
