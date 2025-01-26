#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Callable, Protocol, Tuple, Dict
import numpy as np
from scipy import signal

from raman_fitting.models.spectrum import SpectrumData


class IntensityProcessor(Protocol):
    def process_intensity(self, intensity: np.ndarray) -> np.ndarray: ...


@dataclass
class IntensityFilter:
    name: str
    filter_func: Callable
    filter_args: Tuple
    filter_kwargs: Dict

    def process_intensity(self, intensity: np.ndarray) -> np.ndarray:
        if intensity is None:
            raise ValueError("no intensity given to filter")
        filtered_intensity = self.filter_func(
            intensity, *self.filter_args, **self.filter_kwargs
        )
        return filtered_intensity


available_filters = {
    "savgol_filter": IntensityFilter(
        "savgol_filter",
        signal.savgol_filter,
        filter_args=(13, 3),
        filter_kwargs=dict(mode="nearest"),
    )
}


def filter_spectrum(
    spectrum: SpectrumData | None = None, filter_name="savgol_filter"
) -> SpectrumData:
    if filter_name not in available_filters:
        raise ValueError(f"Chosen filter {filter_name} not available.")
    if spectrum is None:
        raise ValueError("Spectrum is None.")

    filter_class = available_filters[filter_name]
    filtered_intensity = filter_class.process_intensity(spectrum.intensity)
    label = f"{filter_name}_{spectrum.label}"
    filtered_spectrum = spectrum.model_copy(
        update={"intensity": filtered_intensity, "label": label}
    )
    return filtered_spectrum


"""
Parameters
----------
ramanshift : array or list
    collection of the ramanshift values
intensity : array or list
    collection of the intensity values
label : TYPE, optional
    DESCRIPTION. The default is "".
**kwargs : TYPE
    DESCRIPTION.

Returns
-------
None.
"""
