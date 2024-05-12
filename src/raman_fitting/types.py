from typing import TypeAlias, Dict

from raman_fitting.models.fit_models import SpectrumFitModel


SpectrumFitModelCollection: TypeAlias = Dict[str, Dict[str, SpectrumFitModel]]
