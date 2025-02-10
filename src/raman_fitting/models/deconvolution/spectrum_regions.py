from enum import StrEnum
from typing import Dict

from loguru import logger
from pydantic import BaseModel, ValidationError
from raman_fitting.config.load_config_from_toml import load_config_from_toml_files


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
    for region_name, region_data in default_regions_from_file.items():
        try:
            if "limits" not in region_data:
                raise ValueError(
                    f"Region definition for {region_name} requires limits. Missing from {region_data.keys()}"
                )
            region_limits = region_data.get("limits", {})

            valid_region = SpectrumRegionLimits(name=region_name, **region_limits)
            default_regions[region_name] = valid_region
        except ValidationError as e:
            logger.error(f"Region definition for {region_name} is not valid: {e}")
    sorted_regions = sorted(default_regions.values(), key=lambda x: x.min, reverse=True)
    sorted_default_regions = {i.name: i for i in sorted_regions}
    return sorted_default_regions


# Assuming get_default_regions_from_toml_files() returns a dictionary
DEFAULT_REGION_NAMES_FROM_TOML = get_default_regions_from_toml_files().keys()
DEFAULT_REGION_NAME_FALLBACK = {"full", "first_order", "second_order"}
DEFAULT_REGION_NAME_KEYS = (
    DEFAULT_REGION_NAMES_FROM_TOML or DEFAULT_REGION_NAME_FALLBACK
)


class RegionNamesMeta(type(StrEnum)):
    def __new__(metacls, cls, bases, classdict):
        for key in DEFAULT_REGION_NAME_KEYS:
            classdict[key.upper()] = key
        return super().__new__(metacls, cls, bases, classdict)


class RegionNames(StrEnum, metaclass=RegionNamesMeta):
    @classmethod
    def choices(cls) -> list[str]:
        return [member.value for member in cls]
