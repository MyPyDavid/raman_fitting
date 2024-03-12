from enum import StrEnum
from typing import List, Optional, Dict

from loguru import logger
from pydantic import (
    BaseModel,
    ConfigDict,
    InstanceOf,
    Field,
    field_validator,
    model_validator,
    ValidationError,
)
from lmfit import Parameters
from lmfit.models import Model

from raman_fitting.models.deconvolution.lmfit_parameter import (
    LMFIT_MODEL_MAPPER,
    LMFitParameterHints,
    parmeter_to_dict,
)
from raman_fitting.config.default_models import load_config_from_toml_files
from raman_fitting.utils.string_operations import prepare_text_from_param

ParamHintDict = Dict[str, Dict[str, Optional[float | bool | str]]]


class BasePeakWarning(UserWarning):  # pragma: no cover
    pass


PEAK_TYPE_OPTIONS = StrEnum("PEAK_TYPE_OPTIONS", ["Lorentzian", "Gaussian", "Voigt"])


def get_lmfit_model_from_peak_type(peak_type: str, prefix: str = "") -> Optional[Model]:
    """returns the lmfit model instance according to the chosen peak type and sets the prefix from peak_name"""
    model = None

    capitalized = peak_type.capitalize()
    try:
        lmfit_model_class = LMFIT_MODEL_MAPPER[capitalized]
        model = lmfit_model_class(prefix=prefix)
    except IndexError:
        raise NotImplementedError(
            f'This peak type or model "{peak_type}" has not been implemented.'
        )
    return model


class BasePeak(BaseModel):
    """
    --------
    Example usage
    --------
    Base class for easier definition of typical intensity peaks found in the
    raman spectra.

    The go al of is this metaclass is to be able to more easily write
    peak class definitions (for possible user input). It tries to find three
    fields in the definition, which are requiredfor a LMfit model creation,
    namely: peak_name, peak_type and the param hints.

    peak_name:
        arbitrary name as prefix for the peak
    peak_type:
        defines the lineshape of the peak, the following options are implemented:
        "Lorentzian", "Gaussian", "Voigt"
    params_hints:
        initial values for the parameters of the peak, at least
        a value for the center position of the peak should be given.

    It tries to find these fields in different sources such as: the class definition
    with only class attributes, init attributes or even in the keywords arguments.
    The FieldsTracker class instance (fco) keeps track of the definition in different
    sources and can check when all are ready. If there are multiple sources with definitions
    for the same field than the source with highest priority will be chosen (based on tuple order).
    Each field is a propery which validates the assigments.

    Sort of wrapper for lmfit.model definition.
    Several of these peaks combined are used to make the lmfit CompositeModel
    (composed in the fit_models module), which will be used for the fit.

    --------
    Example usage
    --------

    "Example class definition with attribute definitions"
    class New_peak(metaclass=BasePeak):
        "New peak child class for easier definition"

        param_hints = { 'center': {'value': 2435,'min': 2400, 'max': 2550}}
        peak_type = 'Voigt' #'Voigt'
        peak_name ='R2D2'

    New_peak().lmfit_model == <lmfit.Model: Model(voigt, prefix='R2D2_')>

    "Example class definition with keyword arguments"

    New_peak = BasePeak('new',
                        peak_name='D1',
                        peak_type= 'Lorentzian',
                        param_hints = { 'center': {'value': 1500}}
    )
    New_peak()
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)

    peak_name: str
    param_hints: Optional[Parameters | List[LMFitParameterHints] | ParamHintDict] = None
    peak_type: Optional[str] = None
    is_substrate: Optional[bool] = False
    is_for_normalization: Optional[bool] = False
    docstring: Optional[str] = Field(None, repr=False)
    lmfit_model: Optional[InstanceOf[Model]] = None

    @field_validator("peak_type")
    @classmethod
    def check_peak_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if isinstance(v, str):
            try:
                v = PEAK_TYPE_OPTIONS[v].name
                return v
            except KeyError:
                raise KeyError(
                    f"peak_type is not in {map(lambda x: x.name, PEAK_TYPE_OPTIONS)}, but {v}"
                )
        elif isinstance(v, PEAK_TYPE_OPTIONS):
            v = v.name
            return v
        else:
            raise TypeError(f"peak_type is not a string or enum, but {type(v)}")

    @field_validator("param_hints")
    @classmethod
    def check_param_hints(
        cls, v: Optional[Parameters | List[LMFitParameterHints] | ParamHintDict]
    ) -> Optional[Parameters]:
        if v is None:
            return v
        if isinstance(v, Parameters):
            return v

        if isinstance(v, dict):
            valid_p_hints = [LMFitParameterHints(name=k, **val) for k, val in v.items()]

        if isinstance(v, list):
            assert all(isinstance(i, LMFitParameterHints) for i in v)

        pars_hints = [i.parameter for i in valid_p_hints]
        params = Parameters()
        params.add_many(*pars_hints)
        return params

    @model_validator(mode="after")
    def check_lmfit_model(self) -> "BasePeak":
        if self.lmfit_model is not None:
            if isinstance(self.lmfit_model, Model):
                return self
            else:
                raise ValueError(
                    f"lmfit_model is not a Model instance, but {type(self.lmfit_model)}"
                )
        peak_type = self.peak_type
        if peak_type is None:
            raise ValueError("peak_type is None")

        lmfit_model = get_lmfit_model_from_peak_type(
            peak_type, prefix=self.peak_name_prefix
        )
        if lmfit_model is None:
            raise ValueError("lmfit_model is None")

        if self.param_hints is not None:
            for k, v in self.param_hints.items():
                par_dict = parmeter_to_dict(v)
                lmfit_model.set_param_hint(k, **par_dict)
        self.lmfit_model = lmfit_model
        return self

    @property
    def peak_name_prefix(self):
        if not self.peak_name:
            return ""
        if self.peak_name.endswith("_"):
            return self.peak_name
        return self.peak_name + "_"

    def __str__(self):
        _repr = f"{self.__class__.__name__}('{self.peak_name}'"
        if self.lmfit_model is None:
            _repr += ": no Model set"
        _repr += f", {self.lmfit_model}"
        param_text = make_string_from_param_hints(self.param_hints)
        _repr += f"{param_text})"
        return _repr


def make_string_from_param_hints(param_hints: Parameters) -> str:
    param_center = param_hints.get("center", {})
    text = prepare_text_from_param(param_center)
    return text


def get_peaks_from_peak_definitions(
    peak_definitions: Optional[Dict] = None,
) -> Dict[str, BasePeak]:
    if peak_definitions is None:
        peak_definitions = load_config_from_toml_files()
    peak_settings = {
        k: val.get("peaks") for k, val in peak_definitions.items() if "peaks" in val
    }
    peak_models = {}
    for peak_type, peak_type_defs in peak_settings.items():
        if peak_type_defs is None:
            continue
        for peak_name, peak_def in peak_type_defs.items():
            try:
                peak_models[peak_name] = BasePeak(**peak_def)
            except ValidationError as e:
                logger.error(f"Definition:\n{peak_def}\n{e}")

    return peak_models
