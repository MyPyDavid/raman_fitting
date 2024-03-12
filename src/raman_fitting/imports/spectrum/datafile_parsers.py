from typing import Sequence
from pathlib import Path

import numpy as np
import tablib
from tablib import Dataset, detect_format

from loguru import logger


def filter_data_for_numeric(data: Dataset):
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
    dataset: Dataset, header_keys: Sequence[str]
) -> Dataset:
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
    dataset: Dataset, header_keys: Sequence[str]
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


def check_header_keys(dataset: Dataset, header_keys: Sequence[str]):
    if set(header_keys) not in set(dataset.headers):
        first_row = list(dataset.headers)
        dataset.insert(0, first_row)
        dataset.headers = header_keys
    return dataset


def read_file_with_tablib(
    filepath: Path, header_keys: Sequence[str], sort_by=None
) -> Dataset:
    data = load_dataset_from_file(filepath)
    data = validate_columns_with_header_keys(data, header_keys)
    data = check_header_keys(data, header_keys)
    numeric_data = filter_data_for_numeric(data)
    sort_by = header_keys[0] if sort_by is None else sort_by
    sorted_data = numeric_data.sort(sort_by)
    return sorted_data


def read_text(filepath, max_bytes=10**6, encoding="utf-8", errors=None):
    """additional read text method for raw text data inspection"""
    _text = "read_text_method"
    filesize = filepath.stat().st_size
    if filesize < max_bytes:
        try:
            _text = filepath.read_text(encoding=encoding, errors=errors)
            # _text.splitlines()
        except Exception as exc:
            # IDEA specify which Exceptions are expected
            _text += "\nread_error"
            logger.warning(f"file read text error => skipped.\n{exc}")
    else:
        _text += "\nfile_too_large"
        logger.warning(f" file too large ({filesize})=> skipped")

    return _text


def use_np_loadtxt(filepath, usecols=(0, 1), **kwargs) -> np.array:
    array = np.array([])
    try:
        array = np.loadtxt(filepath, usecols=usecols, **kwargs)
    except IndexError:
        logger.debug(f"IndexError called np genfromtxt for {filepath}")
        array = np.genfromtxt(filepath, invalid_raise=False)
    except ValueError:
        logger.debug(f"ValueError called np genfromtxt for {filepath}")
        array = np.genfromtxt(filepath, invalid_raise=False)
    except Exception as exc:
        _msg = f"Can not load data from txt file: {filepath}\n{exc}"
        logger.error(_msg)
        raise ValueError(_msg) from exc
    return array
