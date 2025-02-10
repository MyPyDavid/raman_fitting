from typing import Optional

import numpy as np

from ..models.splitter import SplitSpectrum
from ..models.spectrum import SpectrumData
from ..models.fit_models import SpectrumFitModel, LMFitModel

from loguru import logger


def get_simple_normalization_intensity(split_spectrum: SplitSpectrum) -> float:
    norm_spec = split_spectrum.get_region("normalization")
    if norm_spec.intensity.any():
        return np.nanmax(norm_spec.intensity)
    else:
        valid_regions = [
            i for i in split_spectrum.spec_regions.values() if i.intensity.any()
        ]
        max_valid_regions = max([i.intensity.max() for i in valid_regions])
        return max_valid_regions


def get_normalization_factor(
    split_spectrum: SplitSpectrum,
    norm_method="simple",
    normalization_model: LMFitModel = None,
) -> float:
    simple_norm = get_simple_normalization_intensity(split_spectrum)
    normalization_intensity = simple_norm

    if "fit" in norm_method and normalization_model is not None:
        fit_norm = normalizer_fit_model(
            split_spectrum.get_region("normalization"),
            normalization_model=normalization_model,
        )
        if fit_norm is not None:
            normalization_intensity = fit_norm
    norm_factor = 1 / normalization_intensity

    return norm_factor


def normalize_regions_in_split_spectrum(
    split_spectrum: SplitSpectrum, norm_factor: float, label: Optional[str] = None
) -> SplitSpectrum:
    norm_spec_regions = {}
    norm_infos = {}
    label = split_spectrum.spectrum.label if label is None else label
    for region_name, spec in split_spectrum.spec_regions.items():
        norm_label = f"{region_name}_{label}" if region_name not in label else label
        norm_label = f"norm_{norm_label}" if "norm" not in norm_label else norm_label
        # label looks like "norm_regionname_label"
        _data = SpectrumData(
            **{
                "ramanshift": spec.ramanshift,
                "intensity": spec.intensity * norm_factor,
                "label": norm_label,
                "region_name": region_name,
                "source": spec.source,
            }
        )
        norm_spec_regions.update(**{region_name: _data})
        norm_infos.update(**{region_name: {"normalization_factor": norm_factor}})
    norm_spectra = split_spectrum.model_copy(
        update={"spec_regions": norm_spec_regions, "info": norm_infos}
    )
    return norm_spectra


def normalize_split_spectrum(
    split_spectrum: SplitSpectrum = None,
) -> SplitSpectrum:
    "Normalize the spectrum intensity according to normalization method."
    normalization_factor = get_normalization_factor(split_spectrum)
    norm_data = normalize_regions_in_split_spectrum(
        split_spectrum, normalization_factor
    )
    return norm_data


def normalizer_fit_model(
    spectrum: SpectrumData, normalization_model: LMFitModel
) -> float | None:
    spec_fit = SpectrumFitModel(spectrum=spectrum, model=normalization_model)
    spec_fit.run_fit()
    if not spec_fit.fit_result:
        return
    try:
        return spec_fit.fit_result.params["G_height"].value
    except KeyError as e:
        logger.error(e)
