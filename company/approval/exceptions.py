class ApprovalPersistenceError(Exception):
    """Raised when approval request persistence fails."""


class ApprovalRequestNotFoundError(Exception):
    """Raised when an approval request cannot be found."""


class ApprovalRequestDataError(Exception):
    """Raised when approval request data is missing or invalid."""
