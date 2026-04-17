#!/usr/bin/env python3
"""Lightweight regression tests for overpic extraction and rendering."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import fitz

import extract_images


class OverpicExtractionTests(unittest.TestCase):
    def test_parse_includegraphics_and_overpic_events(self):
        block = r"""
        \begin{figure}
          \includegraphics[width=\linewidth]{figures/plain.pdf}
          \begin{overpic}[width=0.8\linewidth]{figures/overlay.pdf}
            \put(10,20){\scriptsize Label}
            \put(-2.5,3.5){\rotatebox{90}{\small Real}}
            \put(70,80){\textcolor{green}{\cmark}}
          \end{overpic}
        \end{figure}
        """

        events = extract_images.parse_graphics_events(block)

        self.assertEqual([event["target"] for event in events], ["figures/plain.pdf", "figures/overlay.pdf"])
        self.assertEqual(events[0]["overlays"], [])
        self.assertEqual([overlay["text"] for overlay in events[1]["overlays"]], ["Label", "Real", "✓"])
        self.assertEqual(events[1]["overlays"][1]["rotation"], 90)
        self.assertEqual(events[1]["overlays"][2]["color_name"], "green")

    def test_render_with_overpic_overlay_writes_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_pdf = tmp_path / "base.pdf"
            output_png = tmp_path / "out.png"

            doc = fitz.open()
            page = doc.new_page(width=200, height=120)
            page.draw_rect(fitz.Rect(20, 20, 180, 100), color=(0, 0, 0), width=1)
            doc.save(source_pdf)
            doc.close()

            overlays = extract_images.parse_put_overlays(
                r"\put(10,20){\scriptsize Bottom Label}"
                r"\put(70,80){\textcolor{red}{\xmark}}"
                r"\put(-2,50){\rotatebox{90}{\small Side}}"
            )
            ok, mode, warnings = extract_images.convert_to_png(source_pdf, output_png, overlays)

            self.assertTrue(ok)
            self.assertEqual(mode, "pdf_rendered_with_overpic_overlay")
            self.assertEqual(warnings, [])
            self.assertTrue(output_png.exists())
            self.assertGreater(output_png.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
