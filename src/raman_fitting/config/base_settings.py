from typing import Dict
from pathlib import Path

from pydantic import (
    Field,
)

from pydantic_settings import BaseSettings

from raman_fitting.models.deconvolution.base_model import BaseLMFitModel
from raman_fitting.models.deconvolution.base_model import (
    get_models_and_peaks_from_definitions,
)
from raman_fitting.models.deconvolution.spectrum_regions import (
    get_default_regions_from_toml_files,
)
from .load_config_from_toml import load_config_from_toml_files
from .path_settings import create_default_package_dir_or_ask, InternalPathSettings
from types import MappingProxyType


def get_default_models_and_peaks_from_definitions():
    models_and_peaks_definitions = load_config_from_toml_files()
    return get_models_and_peaks_from_definitions(models_and_peaks_definitions)


class Settings(BaseSettings):
    default_models: Dict[str, Dict[str, BaseLMFitModel]] = Field(
        default_factory=get_default_models_and_peaks_from_definitions,
        alias="my_default_models",
        init_var=False,
        validate_default=False,
    )
    default_regions: Dict[str, Dict[str, float]] | None = Field(
        default_factory=get_default_regions_from_toml_files,
        alias="my_default_regions",
        init_var=False,
        validate_default=False,
    )
    default_definitions: MappingProxyType | None = Field(
        default_factory=load_config_from_toml_files,
        alias="my_default_definitions",
        init_var=False,
        validate_default=False,
    )

    destination_dir: Path = Field(default_factory=create_default_package_dir_or_ask)
    internal_paths: InternalPathSettings = Field(default_factory=InternalPathSettings)
