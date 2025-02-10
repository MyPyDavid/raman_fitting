from dataclasses import dataclass, field
import logging
from typing import Dict

from raman_fitting.config.load_config_from_toml import load_config_from_toml_files
from raman_fitting.models.deconvolution.base_model import (
    get_models_and_peaks_from_definitions,
)
from .base_model import BaseLMFitModel

logger = logging.getLogger(__name__)


@dataclass
class InitializeModels:
    """
    This class will initialize and validate the different fitting models.
    The models are of type lmfit.model.CompositeModel and stored in a dict with names
    for the models as keys.
    """

    model_definitions: dict = field(default_factory=dict)
    peaks: dict = field(default_factory=dict)
    lmfit_models: Dict[str, Dict[str, BaseLMFitModel]] | None = None

    def __post_init__(self):
        self.model_definitions = self.model_definitions or {}
        self.peaks = self.peaks or {}
        self.lmfit_models = self.lmfit_models or {}
        if not self.model_definitions:
            self.model_definitions = load_config_from_toml_files()
        if not self.lmfit_models and self.model_definitions:
            self.lmfit_models = get_models_and_peaks_from_definitions(
                self.model_definitions
            )

    def __repr__(self):
        _t = ", ".join(map(str, self.lmfit_models.keys()))
        _t += "\n"
        _t += "\n".join(map(str, self.lmfit_models.values()))
        return _t


def main():
    from raman_fitting.config.default_models import (
        load_config_from_toml_files,
    )

    model_definitions = load_config_from_toml_files()
    print("model_definitions: ", model_definitions)
    models = InitializeModels()
    print(models)
    # breakpoint()


if __name__ == "__main__":
    main()
