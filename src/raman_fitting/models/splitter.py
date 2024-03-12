from typing import Dict, Any
import numpy as np

from pydantic import BaseModel, model_validator, Field
from .spectrum import SpectrumData
from .deconvolution.spectrum_regions import (
    SpectrumRegionLimits,
    RegionNames,
    get_default_regions_from_toml_files,
)


class SplitSpectrum(BaseModel):
    spectrum: SpectrumData
    region_limits: Dict[str, SpectrumRegionLimits] = Field(None, init_var=None)
    spec_regions: Dict[str, SpectrumData] = Field(None, init_var=None)
    info: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def spit_spectrum_into_regions(self) -> "SplitSpectrum":
        if self.region_limits is None:
            region_limits = get_default_spectrum_region_limits()
            self.region_limits = region_limits

        if self.spec_regions is not None:
            return self
        spec_regions = split_spectrum_data_in_regions(
            self.spectrum.ramanshift,
            self.spectrum.intensity,
            spec_region_limits=self.region_limits,
            label=self.spectrum.label,
            source=self.spectrum.source,
        )
        self.spec_regions = spec_regions
        return self

    def get_region(self, region_name: RegionNames):
        region_name = RegionNames(region_name)
        spec_region_keys = [
            i for i in self.spec_regions.keys() if region_name.name in i
        ]
        if len(spec_region_keys) != 1:
            raise ValueError(f"Key {region_name} not in {spec_region_keys}")
        spec_region_key = spec_region_keys[0]
        return self.spec_regions[spec_region_key]


def get_default_spectrum_region_limits(
    regions_mapping: Dict = None,
) -> Dict[str, SpectrumRegionLimits]:
    if regions_mapping is None:
        regions_mapping = get_default_regions_from_toml_files()
    regions = {}
    for region_name, region_config in regions_mapping.items():
        regions[region_name] = SpectrumRegionLimits(name=region_name, **region_config)
    return regions


def split_spectrum_data_in_regions(
    ramanshift: np.array,
    intensity: np.array,
    spec_region_limits=None,
    label=None,
    source=None,
) -> Dict[str, SpectrumData]:
    """
    For splitting of spectra into the several SpectrumRegionLimits,
    the names of the regions are taken from SpectrumRegionLimits
    and set as attributes to the instance.
    """
    if spec_region_limits is None:
        spec_region_limits = get_default_spectrum_region_limits()
    spec_regions = {}
    for region_name, region in spec_region_limits.items():
        # find indices of region in ramanshift array
        ind = (ramanshift >= np.min(region.min)) & (ramanshift <= np.max(region.max))
        region_lbl = f"region_{region_name}"
        if label is not None and label not in region_lbl:
            region_lbl = f"{label}_{region_lbl}"
        _data = {
            "ramanshift": ramanshift[ind],
            "intensity": intensity[ind],
            "label": region_lbl,
            "region_name": region_name,
            "source": source,
        }
        spec_regions[region_lbl] = SpectrumData(**_data)
    return spec_regions
