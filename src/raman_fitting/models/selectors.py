from typing import Sequence

from raman_fitting.models.deconvolution.base_model import LMFitModelCollection
from raman_fitting.models.deconvolution.spectrum_regions import RegionNames


def select_models_from_provided_models(
    region_names: Sequence[RegionNames],
    provided_models: LMFitModelCollection,
    model_names: Sequence[str] | None = None,
) -> LMFitModelCollection:
    """Select certain models from a provided collection"""
    selected_models = {}
    for region_name, all_region_models in provided_models.items():
        if region_name not in {i.value for i in region_names}:
            continue
        if not model_names:
            selected_models[region_name] = all_region_models
            continue
        selected_region_models = {}
        for mod_name, mod_val in all_region_models.items():
            if mod_name not in model_names:
                continue
            selected_region_models[mod_name] = mod_val

        selected_models[region_name] = selected_region_models
    return selected_models
