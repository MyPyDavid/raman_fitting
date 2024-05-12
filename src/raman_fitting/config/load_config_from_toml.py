from pathlib import Path
from types import MappingProxyType
import tomllib


def load_config_from_toml_files() -> MappingProxyType:
    current_parent_dir = Path(__file__).resolve().parent
    config_definitions = {}
    for i in current_parent_dir.glob("*.toml"):
        toml_data = tomllib.loads(i.read_bytes().decode())
        breakpoint()
        if not config_definitions:
            config_definitions = toml_data
            continue
        config_definitions = {**config_definitions, **toml_data}
    if not config_definitions:
        raise ValueError("default models should not be empty.")
    return MappingProxyType(config_definitions)
