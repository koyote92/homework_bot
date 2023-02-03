#!homework_bot/exceptions.py
class EnvironmentalVariableException(Exception):
    """Raised when the environment variable is missing or invalid."""
    pass


class APIException(Exception):
    """Raised when the API is not available."""
    pass
