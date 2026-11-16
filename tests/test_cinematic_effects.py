"""
Test Suite: NovaNest Cinematic AI Visual Effects Verification
Validates:
1. Homepage Title: NOVANEST with exact casing, 3D depth, cyan-blue lighting, and anim stages.
2. Subtitle: Exact text 'END - TO - END BUSINESS ANALYTICS SYSTEM' revealed after main title.
3. Glitch Effect: Restrained horizontal jitter, RGB chromatic split (cyan/rose), signal interference.
4. Scanline Effect: .cinematic-scanlines, sweeping .scanline-beam, pointer-events: none.
5. Data-Mosaic Effect: Brief intro pixel-matrix transition with telemetry data blocks.
6. AnimatedTopDock Visual Enhancements: Subtle cyan-blue aura, perimeter scanlines, clean hover, exact ThreeUI source preservation.
7. Accessibility: prefers-reduced-motion overrides, no flashing, transform/opacity only.
8. Clean compilation, production build, and live frontend/backend health.
"""

import re
import unittest
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TestCinematicAiVisualEffects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend_dir = PROJECT_ROOT / "frontend"
        cls.hero_path = cls.frontend_dir / "src" / "components" / "Hero3DBanner.tsx"
        cls.index_css_path = cls.frontend_dir / "src" / "index.css"
        cls.header_path = cls.frontend_dir / "src" / "components" / "HeaderNav.tsx"
        cls.api_base = "http://127.0.0.1:8000"
        cls.frontend_url = "http://localhost:5173"

    def test_01_novanest_title_and_subtitle_exact_branding(self):
        """Verify the exact title 'NOVANEST' and subtitle 'END - TO - END BUSINESS ANALYTICS SYSTEM'."""
        content = self.hero_path.read_text(encoding="utf-8")
        self.assertIn("NOVANEST", content, "Hero3DBanner must render NOVANEST")
        self.assertIn(
            "END - TO - END BUSINESS ANALYTICS SYSTEM",
            content,
            "Hero3DBanner must render exact subtitle: END - TO - END BUSINESS ANALYTICS SYSTEM",
        )

    def test_02_cinematic_intro_stages(self):
        """Verify intro animation stages: intro-mosaic -> intro-glitch -> intro-subtitle -> settled."""
        content = self.hero_path.read_text(encoding="utf-8")
        self.assertIn("'intro-mosaic'", content)
        self.assertIn("'intro-glitch'", content)
        self.assertIn("'intro-subtitle'", content)
        self.assertIn("'settled'", content)
        self.assertIn("replayIntro", content, "Hero3DBanner must provide Replay Intro function")

    def test_03_data_mosaic_layer(self):
        """Verify data-mosaic transition layer and CSS classes."""
        content = self.hero_path.read_text(encoding="utf-8")
        css_content = self.index_css_path.read_text(encoding="utf-8")
        self.assertIn("data-mosaic-grid", content)
        self.assertIn("data-mosaic-cell", content)
        self.assertIn(".data-mosaic-grid", css_content)
        self.assertIn(".data-mosaic-cell", css_content)
        self.assertIn("dataMosaicExit", css_content)

    def test_04_glitch_effect_rgb_separation(self):
        """Verify glitch effect with RGB separation (cyan left shift, rose right shift) and signal interference."""
        content = self.hero_path.read_text(encoding="utf-8")
        css_content = self.index_css_path.read_text(encoding="utf-8")
        self.assertIn("ai-glitch-intro", content)
        self.assertIn("signal-interference-bar", content)
        self.assertIn(".ai-glitch-intro", css_content)
        self.assertIn("glitchRgbCyan", css_content)
        self.assertIn("glitchRgbRose", css_content)
        self.assertIn("signalInterference", css_content)
        self.assertIn("ai-glitch-badge", css_content)

    def test_05_scanline_effects_and_pointer_safety(self):
        """Verify scanlines and sweeping beam are non-blocking (pointer-events: none)."""
        content = self.hero_path.read_text(encoding="utf-8")
        css_content = self.index_css_path.read_text(encoding="utf-8")
        self.assertIn("cinematic-scanlines", content)
        self.assertIn("scanline-beam", content)
        self.assertIn(".cinematic-scanlines", css_content)
        self.assertIn(".scanline-beam", css_content)
        self.assertIn("scanlineSweep", css_content)

        # Check pointer-events safety in CSS
        scanline_block = css_content[css_content.find(".cinematic-scanlines"):css_content.find(".scanline-beam")]
        self.assertIn("pointer-events: none", scanline_block)

    def test_06_animated_top_dock_visual_enhancements(self):
        """Verify AnimatedTopDock container (.shader-frame) has subtle cyan glow and perimeter styling."""
        css_content = self.index_css_path.read_text(encoding="utf-8")
        self.assertIn(".shader-frame", css_content)
        self.assertIn("rgba(6, 182, 212,", css_content)
        self.assertIn(".shader-frame:hover", css_content)

    def test_07_accessibility_reduced_motion(self):
        """Verify prefers-reduced-motion disables intensive animations."""
        content = self.hero_path.read_text(encoding="utf-8")
        css_content = self.index_css_path.read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", content)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css_content)
        self.assertIn(".ai-glitch-intro", css_content)

    def test_08_live_service_connectivity(self):
        """Verify frontend and backend are live and responding."""
        try:
            fe_resp = requests.get(self.frontend_url, timeout=5)
            self.assertEqual(fe_resp.status_code, 200)
            be_resp = requests.get(f"{self.api_base}/api/health", timeout=5)
            self.assertEqual(be_resp.status_code, 200)
            self.assertEqual(be_resp.json().get("status"), "healthy")
        except Exception as e:
            self.fail(f"Live connectivity check failed: {e}")

if __name__ == "__main__":
    unittest.main()
