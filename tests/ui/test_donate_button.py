"""The donate button in the header tray.

The seam in fulcrum.ui.links is replaced in every test that presses the
button, so the suite never opens a real browser.
"""

from __future__ import annotations

import pytest

from fulcrum.ui import links
from fulcrum.ui.header_buttons import DONATE_TOOLTIP
from fulcrum.ui.header_tray import (
    DONATE_REFUSED_TEXT,
    DONATE_REFUSED_TITLE,
    HeaderTray,
    TrayHandlers,
)
from fulcrum.ui.theme_palettes import THEME_DARK
from fulcrum.version import DONATE_URL

# Written out in full on purpose: a typo in the payment address must fail
# here rather than send a supporter to a page that is not the author's.
FULCRUM_DONATE_URL = "https://www.paypal.com/ncp/payment/X2U2V8TML89DE"


def _nothing() -> None:
    """A tray handler with nothing to do in these tests."""


def _tray(informed: list[tuple[str, str]]) -> HeaderTray:
    return HeaderTray(
        THEME_DARK,
        TrayHandlers(
            model_org=_nothing,
            edit_org=_nothing,
            show_guide=_nothing,
            move_record=_nothing,
            provenance=_nothing,
            presentation=_nothing,
            toggle_theme=_nothing,
            glossary=_nothing,
            inform=lambda title, text: informed.append((title, text)),
        ),
    )


@pytest.fixture
def asked(monkeypatch) -> list[str]:
    """Every address handed to the desktop; the desktop accepts each one."""
    addresses: list[str] = []

    def accept(address: str) -> bool:
        addresses.append(address)
        return True

    monkeypatch.setattr(links, "open_externally", accept)
    return addresses


def test_the_button_sits_immediately_left_of_the_theme_toggle(qapp) -> None:
    tray = _tray([])
    drawn = [tray.row.itemAt(i).widget() for i in range(tray.row.count())]
    drawn = [widget for widget in drawn if widget is not None]
    assert drawn.index(tray.donate_button) + 1 == drawn.index(tray.theme_toggle)
    ring = tray.ring_stops()
    assert ring.index(tray.donate_button) + 1 == ring.index(tray.theme_toggle)
    assert ring == tuple(drawn)
    assert tray.donate_button.isEnabled()
    assert not tray.donate_button.icon().isNull()
    assert tray.donate_button.toolTip() == DONATE_TOOLTIP
    assert "opens your browser" in tray.donate_button.toolTip()


def test_pressing_it_asks_the_desktop_for_that_one_address(qapp, asked) -> None:
    informed: list[tuple[str, str]] = []
    tray = _tray(informed)
    tray.donate_button.click()
    assert asked == [FULCRUM_DONATE_URL]
    assert informed == []


def test_the_address_is_fulcrums_own_and_secure() -> None:
    assert DONATE_URL == FULCRUM_DONATE_URL
    assert DONATE_URL.startswith("https://")


def test_a_desktop_that_refuses_says_so(qapp, monkeypatch) -> None:
    monkeypatch.setattr(links, "open_externally", lambda address: False)
    informed: list[tuple[str, str]] = []
    tray = _tray(informed)
    tray.donate_button.click()
    assert informed == [(DONATE_REFUSED_TITLE, DONATE_REFUSED_TEXT)]
    assert "Could not open a browser" in DONATE_REFUSED_TEXT
    assert DONATE_URL in DONATE_REFUSED_TEXT
