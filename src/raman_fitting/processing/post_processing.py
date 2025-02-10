from dataclasses import dataclass
from typing import Protocol, Dict


from raman_fitting.models.spectrum import SpectrumData

from .baseline_subtraction import subtract_baseline_from_split_spectrum
from .filter import filter_spectrum
from .despike import despike_spectrum_data
from ..models.deconvolution.spectrum_regions import SpectrumRegionLimits
from ..models.splitter import SplitSpectrum
from .normalization import normalize_split_spectrum


class PreProcessor(Protocol):
    def process_spectrum(self, spectrum: SpectrumData | None = None): ...


class PostProcessor(Protocol):
    def process_spectrum(self, split_spectrum: SplitSpectrum | None = None): ...


@dataclass
class SpectrumProcessor:
    """performs  pre-processing, post-, and"""

    spectrum: SpectrumData
    region_limits: Dict[str, SpectrumRegionLimits] | None
    processed: bool = False
    clean_spectrum: SplitSpectrum | None = None

    def __post_init__(self):
        processed_spectrum = self.process_spectrum()
        self.clean_spectrum = processed_spectrum
        self.processed = True

    def process_spectrum(self) -> SplitSpectrum:
        pre_processed_spectrum = self.pre_process_intensity(spectrum=self.spectrum)
        split_spectrum = self.split_spectrum(spectrum=pre_processed_spectrum)
        post_processed_spectra = self.post_process_spectrum(
            split_spectrum=split_spectrum
        )
        return post_processed_spectra

    def pre_process_intensity(
        self, spectrum: SpectrumData | None = None
    ) -> SpectrumData:
        if spectrum is None:
            raise ValueError("Can not pre-process, spectrum is None")
        return despike_spectrum_data(filter_spectrum(spectrum=spectrum))

    def split_spectrum(self, spectrum: SpectrumData | None = None) -> SplitSpectrum:
        split_spectrum = SplitSpectrum(
            spectrum=spectrum, region_limits=self.region_limits
        )
        return split_spectrum

    def post_process_spectrum(
        self, split_spectrum: SplitSpectrum | None = None
    ) -> SplitSpectrum:
        baseline_subtracted = subtract_baseline_from_split_spectrum(
            split_spectrum=split_spectrum
        )
        normalized_spectra = normalize_split_spectrum(
            split_spectrum=baseline_subtracted
        )
        return normalized_spectra
