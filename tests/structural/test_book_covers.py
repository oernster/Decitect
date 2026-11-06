"""The bundled book covers are no taller than the app can ever draw them.

The Book background dialog scales each cover to a fixed height times the UI
scale, which tops out at ui_scale.MAX_FACTOR. A cover taller than twice that
(the headroom for a high-DPI screen) only adds to the download: the original
covers were five times taller and made up a seventh of the installer.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from decitect.ui import ui_scale
from decitect.ui.widgets import book_background_dialog as dialog

_COVER_DIR = Path(__file__).resolve().parents[2] / "assets" / "books"
_HIDPI_HEADROOM = 2


def max_cover_height() -> int:
    """The tallest cover worth shipping, from the dialog's own sizes."""
    tallest = max(dialog._FEATURED_COVER_HEIGHT, dialog._SERIES_COVER_HEIGHT)
    return round(tallest * ui_scale.MAX_FACTOR * _HIDPI_HEADROOM)


def oversized_covers(cover_dir: Path) -> list[str]:
    """Covers in cover_dir taller than max_cover_height, with their heights."""
    limit = max_cover_height()
    found = []
    for path in sorted(cover_dir.glob("*.png")):
        with Image.open(path) as image:
            if image.height > limit:
                found.append(f"{path.name}: {image.height}px")
    return found


def test_covers_exist():
    assert sorted(_COVER_DIR.glob("*.png"))


def test_no_cover_is_taller_than_the_app_can_draw():
    assert oversized_covers(_COVER_DIR) == []


def test_an_oversized_cover_is_caught(tmp_path):
    Image.new("RGB", (1, max_cover_height() + 1)).save(tmp_path / "big.png")
    Image.new("RGB", (1, max_cover_height())).save(tmp_path / "fits.png")
    assert oversized_covers(tmp_path) == [f"big.png: {max_cover_height() + 1}px"]
