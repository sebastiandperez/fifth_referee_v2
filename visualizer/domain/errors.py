from __future__ import annotations

class DomainError(Exception):
    """Base class for domain errors."""

class NotFound(DomainError):
    """A requested domain entity was not found."""

class ValidationError(DomainError):
    """A domain invariant or validation failed."""

class InvariantError(DomainError):
    """A stronger form of validation error for aggregate invariants."""
