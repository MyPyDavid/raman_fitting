"""
Created on Mon Jul  5 21:09:06 2021

@author: DW
"""

from dataclasses import dataclass, field
import hashlib

from pathlib import Path


from raman_fitting.imports.files.validators import validate_filepath
from raman_fitting.imports.spectrum.parse_spectrum import parse_spectrum_from_file
from raman_fitting.models.spectrum import SpectrumData

from loguru import logger


@dataclass
class SpectrumReader:
    """
    Reads a spectrum from a 'raw' data file Path or str

    with spectrum_data_keys "ramanshift" and "intensity".
    Double checks the values
    Sets a hash attribute afterwards
    """

    filepath: Path | str

    spectrum: SpectrumData | None = field(default=None)
    label: str = "raw"
    region_name: str = "full"
    spectrum_hash: str | None = field(default=None, repr=False)
    spectrum_length: int = field(default=0, init=False)

    def __post_init__(self):
        super().__init__()

        self.filepath = validate_filepath(self.filepath)
        self.spectrum_length = 0

        if self.filepath is None:
            raise ValueError(f"File is not valid. {self.filepath}")

        spectrum = parse_spectrum_from_file(
            file=self.filepath,
            label=self.label,
            region_name=self.region_name,
        )
        self.spectrum = spectrum

        self.spectrum_hash = self.get_hash_text(self.spectrum)
        self.spectrum_length = len(self.spectrum)

    @staticmethod
    def get_hash_text(data, hash_text_encoding="utf-8"):
        text = str(data)
        text_hash = hashlib.sha256(text.encode(hash_text_encoding)).hexdigest()
        return text_hash

    def __repr__(self):
        _txt = f"Spectrum({self.filepath.name}, len={self.spectrum_length})"
        return _txt

    def quickplot(self):
        """Plot for quickly checking the spectrum"""
        try:
            self.spectrum.plot(x="ramanshift", y="intensity")
        except TypeError:
            logger.warning("No numeric data to plot")
