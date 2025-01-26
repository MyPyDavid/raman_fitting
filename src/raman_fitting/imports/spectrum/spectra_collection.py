from typing import List

import numpy as np

from pydantic import BaseModel, ValidationError, model_validator

from raman_fitting.models.deconvolution.spectrum_regions import RegionNames
from raman_fitting.models.spectrum import SpectrumData


class SpectraDataCollection(BaseModel):
    spectra: List[SpectrumData]
    region_name: RegionNames
    mean_spectrum: SpectrumData | None = None

    @model_validator(mode="after")
    def check_spectra_have_same_label(self) -> "SpectraDataCollection":
        """checks member of lists"""
        labels = set(i.label for i in self.spectra)
        if len(labels) > 1:
            raise ValidationError(f"Spectra have different labels {labels}")
        return self

    @model_validator(mode="after")
    def check_spectra_have_same_region(self) -> "SpectraDataCollection":
        """checks member of lists"""
        region_names = set(i.region_name for i in self.spectra)
        if len(region_names) > 1:
            raise ValidationError(f"Spectra have different region_names {region_names}")
        return self

    @model_validator(mode="after")
    def check_spectra_lengths(self) -> "SpectraDataCollection":
        unique_lengths_rs = set(len(i.ramanshift) for i in self.spectra)
        unique_lengths_int = set(len(i.intensity) for i in self.spectra)
        if len(unique_lengths_rs) > 1:
            raise ValidationError(
                f"The spectra have different ramanshift lengths where they should be the same.\n\t{unique_lengths_rs}"
            )
        if len(unique_lengths_int) > 1:
            raise ValidationError(
                f"The spectra have different intensity lengths where they should be the same.\n\t{unique_lengths_int}"
            )

        return self

    @model_validator(mode="after")
    def set_mean_spectrum(self) -> "SpectraDataCollection":
        # wrap this in a ProcessedSpectraCollection model
        mean_int = np.mean(np.vstack([i.intensity for i in self.spectra]), axis=0)
        mean_ramanshift = np.mean(
            np.vstack([i.ramanshift for i in self.spectra]), axis=0
        )
        source_files = set(i.source for i in self.spectra)
        _label = "".join(map(str, set(i.label for i in self.spectra)))
        mean_spec = SpectrumData(
            ramanshift=mean_ramanshift,
            intensity=mean_int,
            label=f"clean_{self.region_name}_mean",
            region_name=self.region_name,
            source=source_files,
        )
        self.mean_spectrum = mean_spec
        return self
