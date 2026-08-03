"""Exception types raised by the price tracker."""


class PriceTrackerError(Exception):
    """Base class for all errors raised by this application."""


class ConfigError(PriceTrackerError):
    """Raised when configuration is missing or invalid."""


class DatabaseError(PriceTrackerError):
    """Raised when a database operation fails."""


class ScraperError(PriceTrackerError):
    """Raised when a retailer scraper cannot complete an operation."""


class EbayAPIError(PriceTrackerError):
    """Raised when the eBay API cannot be reached or returns bad data."""


class NotificationError(PriceTrackerError):
    """Raised when a Discord notification cannot be delivered."""
