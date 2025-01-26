"""
Created on Mon May  3 11:10:59 2021

@author: dw
"""

from typing import Dict, Tuple, Any, Optional
import copy
import logging

import numpy as np

from pydantic import BaseModel, Field, model_validator

from raman_fitting.models.spectrum import SpectrumData

logger = logging.getLogger(__name__)


class SpectrumDespiker(BaseModel):
    spectrum: Optional[SpectrumData] = None
    threshold_z_value: int = 4
    moving_region_size: int = 1
    ignore_lims: Tuple[int, int] = (20, 46)
    info: Dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def process_spectrum(self) -> "SpectrumDespiker":
        if self.spectrum is None:
            raise ValueError("SpectrumDespiker, spectrum is None")
        despiked_intensity, result_info = self.call_despike_spectrum(
            self.spectrum.intensity
        )
        despiked_spec = self.spectrum.model_copy(
            update={"intensity": despiked_intensity}, deep=True
        )
        SpectrumData.model_validate(despiked_spec, from_attributes=True)
        self._processed_spectrum = despiked_spec
        self.info.update(**result_info)
        return self

    @property
    def processed_spectrum(self) -> SpectrumData:
        if not hasattr(self, "_processed_spectrum"):
            raise ValueError(
                "Processed spectrum is not available. Ensure the model is properly initialized."
            )
        return self._processed_spectrum

    def process_intensity(self, intensity: np.ndarray) -> np.ndarray:
        despiked_intensity, _ = self.call_despike_spectrum(intensity)
        return despiked_intensity

    def call_despike_spectrum(self, intensity: np.ndarray) -> Tuple[np.ndarray, Dict]:
        despiked_intensity, result_info = despike_spectrum_intensity(
            intensity,
            self.threshold_z_value,
            self.moving_region_size,
            ignore_lims=self.ignore_lims,
        )
        return despiked_intensity, result_info


def despike_spectrum_intensity(
    intensity: np.ndarray,
    threshold_z_value: int,
    moving_region_size: int,
    ignore_lims=(20, 46),
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    A Despiking algorithm from reference literature:
      https://doi.org/10.1016/j.chemolab.2018.06.009

    Parameters
    ----------
    input_intensity : np.ndarray
        The intensity array of which the desipked intensity will be calculated.
    info : dict, optional
        Extra information for despiking settings are added to this dict.
    Attributes
    ---------
    despiked_intensity : np.ndarray
        The resulting array of the despiked intensity of same length as input_intensity.
    Notes
    --------
    Let Y1;...;Yn represent the values of a single Raman spectrum recorded at
    equally spaced wavenumbers.
    From this series, form the detrended differenced seriesr Yt ...:This simple
    data processing step has the effect of annihilating linear and slow movingcurve
    linear trends, however,
    sharp localised spikes will be preserved.Denote the median and the median absolute
    deviation of
    D.A. Whitaker, K. Hayes. Chemometrics and Intelligent Laboratory Systems 179 (2018) 82–84
    """

    z_intensity = calc_z_value_intensity(intensity)
    filtered_z_intensity = filter_z_intensity_values(z_intensity, threshold_z_value)
    i_despiked = despike_filter(
        intensity, filtered_z_intensity, moving_region_size, ignore_lims=ignore_lims
    )
    result = {"z_intensity": z_intensity, "filtered_z_intensity": filtered_z_intensity}
    return i_despiked, result


def calc_z_value_intensity(intensity: np.ndarray) -> np.ndarray:
    diff_intensity = np.append(np.diff(intensity), 0)  # dYt
    median_diff_intensity = np.median(diff_intensity)  # dYt_Median
    median_abs_deviation = np.median(abs(diff_intensity - median_diff_intensity))
    intensity_values_z = (
        0.6745 * (diff_intensity - median_diff_intensity)
    ) / median_abs_deviation
    return intensity_values_z


def filter_z_intensity_values(z_intensity, z_intensityhreshold):
    filtered_z_intensity = copy.deepcopy(z_intensity)
    filtered_z_intensity[np.abs(z_intensity) > z_intensityhreshold] = np.nan
    filtered_z_intensity[0] = filtered_z_intensity[-1] = 0
    return filtered_z_intensity


def despike_filter(
    intensity: np.ndarray,
    filtered_z_intensity: np.ndarray,
    moving_region_size: int,
    ignore_lims=(20, 46),
):
    n = len(intensity)
    i_despiked = copy.deepcopy(intensity)
    spikes = np.nonzero(np.isnan(filtered_z_intensity))
    for i in list(spikes[0]):
        if i < ignore_lims[0] or i > ignore_lims[1]:
            w = np.arange(
                max(0, i - moving_region_size), min(n, i + moving_region_size)
            )
            w = w[~np.isnan(filtered_z_intensity[w])]
            if intensity[w].any():
                i_despiked[i] = np.mean(intensity[w])
            else:
                i_despiked[i] = intensity[i]
    return i_despiked


def despike_spectrum_data(spectrum: SpectrumData) -> SpectrumData:
    return SpectrumDespiker(spectrum=spectrum).processed_spectrum
