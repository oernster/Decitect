"""Type checks the value objects run on their own fields.

An organisation arrives from files the app did not write as often as from
its own editor: an import, a hand-edited autosave, a calibration case. JSON
carries any type in any field and Python's json reads NaN, Infinity and
1e999 without complaint. A range check alone is no guard: NaN fails every
comparison, so `size < 1` is false for it and a NaN team once loaded and
scored a perfect 100. Each check here refuses the wrong type outright with
the domain's own error, so every reader of a file meets one failure type.
"""

from __future__ import annotations

import math

from decitect.domain.errors import InvalidOrgStateError

# The largest whole number the model's float arithmetic holds exactly: an
# IEEE double carries a 53-bit significand. Counts far beyond it overflow
# the scoring arithmetic to infinity and then to NaN (a workload at the
# float maximum measured latency NaN and a score of 100), so a count is
# refused above it. Every real organisation sits many orders below.
_SIGNIFICAND_BITS = 53
MAX_COUNT: int = 2**_SIGNIFICAND_BITS


def require_text(value: object, what: str) -> None:
    """A field that names something must be a string."""
    if not isinstance(value, str):
        raise InvalidOrgStateError(f"{what} must be text")


def require_optional_text(value: object, what: str) -> None:
    """A reference that may be absent must be a string when present."""
    if value is not None:
        require_text(value, what)


def require_flag(value: object, what: str) -> None:
    """A yes-or-no field must be a real boolean, never a truthy string."""
    if not isinstance(value, bool):
        raise InvalidOrgStateError(f"{what} must be true or false")


def require_whole(value: object, what: str) -> None:
    """A count must be a whole number the model can carry exactly.

    bool is an int subclass in Python, so it is refused by name: a file
    holding true for a headcount is malformed, not one person.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidOrgStateError(f"{what} must be a whole number")
    if abs(value) > MAX_COUNT:
        raise InvalidOrgStateError(f"{what} must not exceed {MAX_COUNT}")


def require_finite(value: object, what: str) -> None:
    """A measured quantity must be a finite number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidOrgStateError(f"{what} must be a number")
    # A whole number is always finite and math.isfinite overflows on one
    # past the float range, so only a float is tested.
    if isinstance(value, float) and not math.isfinite(value):
        raise InvalidOrgStateError(f"{what} must be a finite number")


def require_tuple_of(values: object, kind: type, what: str) -> None:
    """A collection must be a tuple holding only its own kind."""
    if not isinstance(values, tuple) or not all(isinstance(v, kind) for v in values):
        raise InvalidOrgStateError(f"{what} must be a tuple of {kind.__name__}")
