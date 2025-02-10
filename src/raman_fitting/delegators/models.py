# pylint: disable=W0614,W0401,W0611,W0622,C0103,E0401,E0402
from typing import Dict, Sequence

from pydantic import BaseModel

from raman_fitting.imports.models import RamanFileInfo

from raman_fitting.models.spectrum import SpectrumData
from raman_fitting.models.fit_models import SpectrumFitModel
from raman_fitting.models.splitter import RegionNames
from raman_fitting.imports.spectrumdata_parser import SpectrumReader
from raman_fitting.processing.post_processing import SpectrumProcessor


class PreparedSampleSpectrum(BaseModel):
    file_info: RamanFileInfo
    read: SpectrumReader
    processed: SpectrumProcessor


class AggregatedSampleSpectrum(BaseModel):
    sources: Sequence[PreparedSampleSpectrum]
    spectrum: SpectrumData


class AggregatedSampleSpectrumFitResult(BaseModel):
    region_name: RegionNames
    aggregated_spectrum: AggregatedSampleSpectrum
    fit_model_results: Dict[str, SpectrumFitModel]
