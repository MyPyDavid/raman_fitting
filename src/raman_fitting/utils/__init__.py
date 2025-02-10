from loguru import logger  # noqa: E402


def version() -> str:
    from raman_fitting.__about__ import __package_name__
    from raman_fitting.__about__ import __version__

    logger.debug(
        f"{__package_name__} version {__version__}"
    )  # logging should be disabled here
    return f"{__package_name__} version {__version__}"
