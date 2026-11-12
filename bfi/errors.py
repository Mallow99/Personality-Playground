"""Expected failures. Their messages are written for the person using the app."""


class AppError(Exception):
    """Something went wrong that the desktop can explain as-is, without a traceback."""

    def __init__(self, message, code="error"):
        self.message, self.code = message, code
        super().__init__(message)
