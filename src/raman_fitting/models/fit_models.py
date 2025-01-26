from typing import Dict
import time

from pydantic import BaseModel, model_validator, Field, ConfigDict
from lmfit import Model as LMFitModel
from lmfit.model import ModelResult

from raman_fitting.config import settings
from raman_fitting.models.deconvolution.base_model import BaseLMFitModel
from raman_fitting.models.deconvolution.spectrum_regions import RegionNames
from raman_fitting.models.post_deconvolution.calculate_params import (
    calculate_ratio_of_unique_vars_in_results,
)

from raman_fitting.models.spectrum import SpectrumData


class SpectrumFitModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    spectrum: SpectrumData
    model: BaseLMFitModel
    region: RegionNames
    fit_kwargs: Dict = Field(default_factory=dict, repr=False)
    fit_result: ModelResult = Field(None, init_var=False)  # TODO move to property
    param_results: Dict = Field(default_factory=dict)
    elapsed_time: float = Field(0, init_var=False, repr=False)

    @model_validator(mode="after")
    def match_region_names(self) -> "SpectrumFitModel":
        model_region = self.model.region_name
        spec_region = self.spectrum.region_name
        if model_region != spec_region:
            raise ValueError(
                f"Region names do not match {model_region} and {spec_region}"
            )
        return self

    @model_validator(mode="after")
    def test_if_spectrum_has_model_region(self) -> "SpectrumFitModel":
        model_region = self.model.region_name
        region_limits = settings.default_regions[model_region]
        center_params = [
            i.param_hints.get("center", {}).get("value", 0)
            for i in self.model.lmfit_model.components
        ]
        if not all(region_limits.min <= i <= region_limits.max for i in center_params):
            raise ValueError("Not all model params fall in the region limits.")
        if not (self.spectrum.ramanshift.any() and self.spectrum.intensity.any()):
            raise ValueError("Spectrum is empty.")
        if not all(
            self.spectrum.ramanshift.min() <= i <= self.spectrum.ramanshift.max()
            for i in center_params
        ):
            raise ValueError(
                "Not all model params are covered by the spectrum ramanshift data."
            )

        return self

    def run_fit(self) -> None:
        if "method" not in self.fit_kwargs:
            self.fit_kwargs["method"] = "leastsq"
        lmfit_model = self.model.lmfit_model
        start_time = time.time()
        fit_result = call_fit_on_model(lmfit_model, self.spectrum, **self.fit_kwargs)
        end_time = time.time()
        elapsed_seconds = abs(start_time - end_time)
        self.elapsed_time = elapsed_seconds
        self.fit_result = fit_result
        self.post_process()

    def post_process(self):
        if not self.fit_result:
            return
        param_results = self.fit_result.params.valuesdict()
        params_ratio_vars = calculate_ratio_of_unique_vars_in_results(
            param_results, raise_exception=False
        )
        self.param_results["ratios"] = params_ratio_vars


def call_fit_on_model(
    model: LMFitModel, spectrum: SpectrumData, method="leastsq", **kwargs
) -> ModelResult:
    # ideas: improve fitting loop so that starting parameters from modelX and modelX+Si are shared, faster...
    init_params = model.make_params()
    x, y = spectrum.ramanshift, spectrum.intensity
    out = model.fit(y, init_params, x=x, method=method, **kwargs)  # 'leastsq'
    return out
