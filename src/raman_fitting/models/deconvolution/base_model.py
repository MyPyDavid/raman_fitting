"""The members of the validated collection of BasePeaks are assembled here into fitting Models"""

from types import MappingProxyType
from typing import Optional, Dict, TypeAlias
from warnings import warn

from lmfit.models import Model as LMFitModel
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    model_validator,
    computed_field,
)


from raman_fitting.models.deconvolution.base_peak import (
    BasePeak,
    get_peaks_from_peak_definitions,
)
from raman_fitting.models.deconvolution.lmfit_parameter import (
    construct_lmfit_model_from_components,
)
from raman_fitting.models.splitter import RegionNames


SEP = "+"
SUFFIX = "_"


class BaseLMFitModelWarning(UserWarning):
    pass


class BaseLMFitModel(BaseModel):
    """
    This Model class combines the collection of valid peaks from BasePeak into a regression model
    of type lmfit.model.CompositeModel
    that is compatible with the lmfit Model and fit functions.
    The model_name, include_substrate and lmfit_model attributes are kept
    consistent w.r.t. their meaning when they are set.

    Parameters
    --------
        verbose_name: string ==> is converted to lmfit Model object
        include_substrate: bool ==> toggle between True and False to include a substrate peak

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(min_length=3, max_length=32)
    peaks: str = Field(min_length=1, max_length=32)
    peak_collection: Dict[str, BasePeak] = Field(
        default_factory=get_peaks_from_peak_definitions,
        validate_default=True,
        repr=False,
    )
    lmfit_model: LMFitModel = Field(None, init_var=False, repr=False)
    region_name: RegionNames

    @computed_field
    @property
    def has_substrate(self) -> bool:
        if not self.lmfit_model.components:
            return False
        comps = set(map(lambda x: x.prefix, self.lmfit_model.components))
        substrate_comps = set(
            [i.lmfit_model.prefix for i in self.substrate_peaks.values()]
        )
        return substrate_comps.issubset(comps)

    def add_substrate(self):
        if self.has_substrate:
            warn(
                f"{self.__class__.__name__} already has substrate.",
                BaseLMFitModelWarning,
            )
            return

        for name in self.substrate_peaks.keys():
            self.peaks += SEP + name
        self.reconstruct_lmfit_model()

    def remove_substrate(self):
        if not self.has_substrate:
            warn(
                f"{self.__class__.__name__} has no substrate to remove.",
                BaseLMFitModelWarning,
            )
            return
        _peaks = self.peaks.split(SEP)
        for name in self.substrate_peaks.keys():
            _peaks.remove(name)
        self.peaks = SEP.join(_peaks)
        self.reconstruct_lmfit_model()

    @computed_field
    @property
    def substrate_peaks(self) -> Dict[str, BasePeak]:
        return {k: val for k, val in self.peak_collection.items() if val.is_substrate}

    @model_validator(mode="after")
    def check_peaks_in_peak_collection(self) -> "BaseLMFitModel":
        peak_names_split = self.peaks.split(SEP)
        default_peak_names = self.peak_collection.keys()
        valid_peaks = set(peak_names_split).union(set(default_peak_names))
        assert valid_peaks
        new_peak_names = SEP.join([i for i in peak_names_split if i in valid_peaks])
        self.peaks = new_peak_names
        return self

    @model_validator(mode="after")
    def check_lmfit_model(self) -> "BaseLMFitModel":
        self.reconstruct_lmfit_model()
        return self

    def reconstruct_lmfit_model(self):
        self.lmfit_model = construct_lmfit_model(self.peaks, self.peak_collection)


def construct_lmfit_model(
    peaks: str, peak_collection: Dict[str, BasePeak]
) -> LMFitModel:
    if not peak_collection:
        raise ValueError("peak collection should not be empty.")
    if not peaks:
        raise ValueError("peaks should not be empty.")
    peak_names = peaks.split(SEP)
    if not peak_names:
        raise ValueError(
            f"could not split any peak names from {peaks} with separator {SEP}."
        )
    base_peaks = [peak_collection[i] for i in peak_names if i in peak_collection]
    if not base_peaks:
        raise ValueError(f"Could not find matching peaks for {peaks}")
    base_peaks_lmfit = [i.lmfit_model for i in base_peaks]
    lmfit_model = construct_lmfit_model_from_components(base_peaks_lmfit)
    return lmfit_model


LMFitModelCollection: TypeAlias = Dict[str, Dict[str, BaseLMFitModel]]


def get_models_and_peaks_from_definitions(
    models_and_peaks_definitions: Optional[MappingProxyType] = None,
) -> LMFitModelCollection:
    region_settings = models_and_peaks_definitions["spectrum"]["regions"]
    all_models = {}
    for region_name, region_model_settings in region_settings.items():
        if region_model_settings is None:
            continue
        all_models[region_name] = {}
        peaks = region_model_settings.get("peaks", {})
        peak_collection = get_peaks_from_peak_definitions(peak_definitions=peaks)
        region_models = region_model_settings.get("models", {})
        for model_name, model_peaks in region_models.items():
            all_models[region_name][model_name] = BaseLMFitModel(
                name=model_name,
                peaks=model_peaks,
                peak_collection=peak_collection,
                region_name=region_name,
            )
    return all_models


def main():
    models = get_models_and_peaks_from_definitions()
    print("Models: ", len(models))


if __name__ == "__main__":
    main()
