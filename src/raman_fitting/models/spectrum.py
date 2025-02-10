import numpy as np

from pydantic import (
    BaseModel,
    FilePath,
    AwareDatetime,
    model_validator,
    Field,
)
import pydantic_numpy.typing as pnd


class SpectrumData(BaseModel):
    ramanshift: pnd.Np1DArrayFp32 = Field(repr=False)
    intensity: pnd.Np1DArrayFp32 = Field(repr=False)
    label: str
    source: FilePath | str | set[FilePath] | set[str]
    region_name: str | None = None

    @model_validator(mode="after")
    def validate_equal_length(self):
        if len(self.ramanshift) != len(self.intensity):
            raise ValueError("Spectrum arrays are not of equal length.")
        return self

    @model_validator(mode="after")
    def check_if_contains_nan(self):
        if np.isnan(self.ramanshift).any():
            raise ValueError("Ramanshift contains NaN")

        if np.isnan(self.intensity).any():
            raise ValueError("Intensity contains NaN")
        return self

    # length is derived property
    def __len__(self):
        return len(self.ramanshift)


class SpectrumMetaData(BaseModel):
    sample_id: str
    sample_group: str
    sample_position: str
    creation_date: AwareDatetime
    source_file: FilePath  # FileStem is derived
