from typing import Sequence
from pathlib import Path

import tablib
from tablib import Dataset, detect_format

from loguru import logger

from raman_fitting.imports.spectrum.datafile_schema import SpectrumDataKeys


DEFAULT_SORT_BY = SpectrumDataKeys.ramanshift


def filter_split_row_for_numeric(data: Dataset):
    filtered_data = Dataset()
    filtered_data.headers = data.headers

    for row in data:
        try:
            digits_row = tuple(map(float, row))
        except ValueError:
            continue
        except TypeError:
            continue

        if not any(i is None for i in digits_row):
            filtered_data.append(digits_row)
    return filtered_data


def load_dataset_from_file(filepath, **kwargs) -> Dataset:
    _format = detect_format(filepath)
    if _format is None:
        _format = "csv"
    with open(filepath, "r") as fh:
        imported_data = Dataset(**kwargs).load(fh, format=_format)
    return imported_data


def ignore_extra_columns(dataset: Dataset, header_keys: Sequence[str]) -> Dataset:
    new_dataset = tablib.Dataset()
    for n, i in enumerate(header_keys):
        new_dataset.append_col(dataset.get_col(n))
    new_dataset.headers = header_keys
    return new_dataset


def split_single_rows_into_columns(
    dataset: Dataset, header_keys: SpectrumDataKeys
) -> Dataset:
    if dataset.width != 1:
        raise ValueError(f"Dataset width should to be 1, not {dataset.width}.")
    col0 = dataset.get_col(0)
    col0_split_rows = list(map(lambda x: x.split(), col0))
    _col0_split_len = set(len(i) for i in col0_split_rows)
    col0_split_cols = list(zip(*col0_split_rows))
    new_dataset = tablib.Dataset()
    for n, i in enumerate(header_keys):
        new_dataset.append_col(col0_split_cols[n])
    new_dataset.headers = header_keys
    return new_dataset


def validate_columns_with_header_keys(
    dataset: Dataset, header_keys: SpectrumDataKeys
) -> Dataset | None:
    if not dataset:
        return dataset
    if dataset.width == 1:
        logger.warning(
            f"data has only a single columns {dataset.width}, splitting into {len(header_keys)}"
        )
        dataset = split_single_rows_into_columns(dataset, header_keys)
    elif dataset.width > len(header_keys):
        logger.warning(
            f"data has too many columns {dataset.width}, taking first {len(header_keys)}"
        )
        dataset = ignore_extra_columns(dataset, header_keys)
    return dataset


def check_header_keys(dataset: Dataset, header_keys: SpectrumDataKeys):
    if set(header_keys) not in set(dataset.headers):
        first_row = list(dataset.headers)
        dataset.insert(0, first_row)
        dataset.headers = header_keys
    return dataset


def read_file_with_tablib(
    filepath: Path,
    header_keys: SpectrumDataKeys | None = None,
    sort_by: str | None = None,
) -> Dataset:
    data = load_dataset_from_file(filepath)
    data = validate_columns_with_header_keys(data, header_keys)
    data = check_header_keys(data, header_keys)
    numeric_data = filter_split_row_for_numeric(data)
    if sort_by is None and DEFAULT_SORT_BY in header_keys:
        sort_by = DEFAULT_SORT_BY

    if sort_by is not None:
        numeric_data = numeric_data.sort(sort_by)

    return numeric_data


def read_text(filepath, max_bytes=10**6, encoding="utf-8", errors=None) -> str:
    """additional read text method for raw text data inspection"""
    _text = "read_text_method"
    file_size = filepath.stat().st_size
    if file_size > max_bytes:
        _text += "\nfile_too_large"
        logger.warning(f" file too large ({file_size})=> skipped")
        return _text
    try:
        _text = filepath.read_text(encoding=encoding, errors=errors)
    except Exception as exc:
        # IDEA specify which Exceptions are expected
        _text += "\nread_error"
        logger.warning(f"file read text error => skipped.\n{exc}")
    return _text
