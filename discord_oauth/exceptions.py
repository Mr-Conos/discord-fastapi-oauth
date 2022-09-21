class DiscordOAuthException(Exception):
    """Base Exception class representing a discord-fastapi-oauth exception."""


class HttpException(DiscordOAuthException):
    """Base Exception class representing an HTTP exception."""


class RateLimited(HttpException):
    """An HTTP Exception raised when the application is being rate limited."""


class Unauthorized(HttpException):
    """An HTTP Exception raised when user is not authorized."""


class AccessDenied(HttpException):
    """Exception raised when user cancels OAuth authorization grant."""


class InvalidStatePassed(DiscordOAuthException):
    """Exception raised when an invalid state is used for a token exchange."""
