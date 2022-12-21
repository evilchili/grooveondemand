
class APIHandlingException(Exception):
    """
    An API reqeust could not be encoded or decoded.
    """


class ThemeMissingException(Exception):
    """
    The specified theme could not be loaded.
    """


class ThemeConfigurationError(Exception):
    """
    A theme is missing required files or configuration.
    """


class ConfigurationError(Exception):
    """
    An error was discovered with the Groove on Demand configuration.
    """


class PlaylistValidationError(Exception):
    """
    An error was discovered in the playlist definition.
    """


class TrackNotFoundError(Exception):
    """
    The specified track doesn't exist.
    """


class InvalidPathError(Exception):
    """
    The specified path was invalid -- either it was not the expected type or wasn't accessible.
    """
