from pathlib import Path
from typing import Sequence

from raman_fitting.models.spectrum import SpectrumData

from loguru import logger

from .datafile_parsers import get_parser_method_for_filetype, get_expected_header_keys
from .validators import spectrum_keys_expected_values


def parse_spectrum_from_file(
    file: Path = None,
    label: str | None = None,
    region_name: str | None = None,
    header_keys: Sequence[str] | None = None,
) -> SpectrumData | None:
    parser = get_parser_method_for_filetype(file)
    if header_keys is None:
        header_keys = get_expected_header_keys()
    parsed_spectrum = parser(file, header_keys=header_keys)
    if parsed_spectrum is None:
        return
    for spectrum_key in parsed_spectrum.headers:
        if spectrum_key not in header_keys:
            continue
        validator = spectrum_keys_expected_values[spectrum_key]
        valid = validator.validate(parsed_spectrum)
        if not valid:
            logger.warning(
                f"The values of {spectrum_key} of this spectrum are invalid. {validator}"
            )
    spec_init = {
        "label": label,
        "region_name": region_name,
        "source": file,
    }
    _parsed_spec_dict = {
        k: parsed_spectrum[k] for k in spectrum_keys_expected_values.keys()
    }
    spec_init.update(_parsed_spec_dict)
    spectrum = SpectrumData(**spec_init)
    return spectrum
