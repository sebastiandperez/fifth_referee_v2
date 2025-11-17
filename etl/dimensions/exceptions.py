class DimensionError(RuntimeError):
    """Base exception for errors while maintaining dimensions."""


class MissingDimensionData(DimensionError):
    """Raised when the raw data required to build dimensions is incomplete."""
