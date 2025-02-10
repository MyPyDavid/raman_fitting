from enum import Enum
from functools import partial
from pathlib import Path
from typing import Callable, Type

from tablib import Dataset

from .datafile_parser_utils import read_file_with_tablib
from .datafile_schema import SpectrumDataKeys

SPECTRUM_FILETYPE_PARSERS = {
    ".txt": {
        "method": read_file_with_tablib,  # load_spectrum_from_txt,
    },
    ".xlsx": {
        "method": read_file_with_tablib,  # pd.read_excel,
    },
    ".csv": {
        "method": read_file_with_tablib,  # pd.read_csv,
    },
    ".json": {
        "method": read_file_with_tablib,
    },
}


def get_expected_header_keys(
    header_keys: Type[SpectrumDataKeys] | None = None,
) -> Type[SpectrumDataKeys] | Type[Enum]:
    if header_keys is None:
        return SpectrumDataKeys
    elif issubclass(header_keys, Enum):
        return header_keys
    else:
        raise ValueError("unknown header keys")


def get_parser_method_for_filetype(
    filepath: Path, **kwargs
) -> Callable[[Path, dict], Dataset]:
    """Get callable file parser function."""
    suffix = filepath.suffix
    parser = SPECTRUM_FILETYPE_PARSERS[suffix]["method"]
    parser_kwargs = SPECTRUM_FILETYPE_PARSERS[suffix].get("kwargs", {})
    kwargs.update(**parser_kwargs)
    if "header_keys" not in kwargs:
        kwargs["header_keys"] = get_expected_header_keys()
    return partial(parser, **kwargs)
