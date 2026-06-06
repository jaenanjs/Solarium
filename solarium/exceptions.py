"""Axon framework exceptions."""


class AxonError(Exception):
    """Base exception for all Axon errors."""


class AgentNotFoundError(AxonError):
    """Raised when a referenced agent does not exist in the network."""


class MaxHandoffsExceeded(AxonError):
    """Raised when handoff limit is exceeded."""


class ToolError(AxonError):
    """Raised when a tool call fails."""
