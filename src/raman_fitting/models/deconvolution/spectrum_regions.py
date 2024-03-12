from enum import StrEnum
from typing import Dict

from loguru import logger
from pydantic import BaseModel, ValidationError
from raman_fitting.config.default_models import load_config_from_toml_files


class SpectrumRegionLimits(BaseModel):
    name: str
    min: int
    max: int
    extra_margin: int = 20


def get_default_regions_from_toml_files() -> Dict[str, SpectrumRegionLimits]:
    default_regions_from_file = (
        load_config_from_toml_files().get("spectrum", {}).get("regions", {})
    )
    default_regions = {}
    for region_name, region_limits in default_regions_from_file.items():
        try:
            valid_region = SpectrumRegionLimits(name=region_name, **region_limits)
            default_regions[region_name] = valid_region
        except ValidationError as e:
            logger.error(f"Region definition for {region_name} is not valid: {e}")
    return default_regions


RegionNames = StrEnum(
    "RegionNames",
    " ".join(get_default_regions_from_toml_files().keys()),
    module=__name__,
)
