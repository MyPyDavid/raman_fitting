from pathlib import Path
from types import MappingProxyType
import tomllib

import tomli_w
from loguru import logger

from .path_settings import INTERNAL_DEFAULT_MODELS

CONFIG_NESTING = ("spectrum", "regions")


def merge(base: dict, update: dict) -> None:
    """Recursively merge `update` into `base` in-place.
    Reference: https://stackoverflow.com/a/77290971
    """
    for k, update_v in update.items():
        base_v = base.get(k)
        if isinstance(base_v, dict) and isinstance(update_v, dict):
            merge(base_v, update_v)
        else:
            base[k] = update_v


def load_config_from_toml_files(config_dir: Path | None = None) -> MappingProxyType:
    if config_dir is None:
        config_dir = INTERNAL_DEFAULT_MODELS
    config_definitions = {}
    toml_files = list(config_dir.rglob("*.toml"))
    for file in toml_files:
        logger.debug(f"Loading config from file: {file}")
        toml_data = tomllib.loads(file.read_bytes().decode())
        if not config_definitions and toml_data:
            config_definitions = toml_data
            continue
        merge(config_definitions, toml_data)
    if not config_definitions:
        raise ValueError("default models should not be empty.")

    try:
        config_definitions["spectrum"]
    except KeyError:
        raise KeyError(
            f"Could not find key 'spectrum' in the config from files:\n{toml_files}"
        )
    return MappingProxyType(config_definitions)


def dump_default_config(target_file: Path) -> None:
    default_config: dict = dict(load_config_from_toml_files())
    with open(target_file, "wb") as f:
        tomli_w.dump(default_config, f)
    logger.info(f"Wrote default config to cwd:{target_file}")
