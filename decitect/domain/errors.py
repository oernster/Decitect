"""Typed domain exception hierarchy for Decitect."""

from __future__ import annotations


class DecitectError(Exception):
    """Base class for all Decitect domain errors."""


class InvalidOrgStateError(DecitectError):
    """Raised when an organisational state violates a structural invariant."""


class InvalidMoveError(DecitectError):
    """Raised when a move cannot be applied to a given state."""


class UnknownTeamError(DecitectError):
    """Raised when a move or dependency references a team that does not exist."""
