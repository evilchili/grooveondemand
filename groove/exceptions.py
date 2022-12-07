
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


class PlaylistImportError(Exception):
    """
    An error was discovered in a playlist template.
    """
