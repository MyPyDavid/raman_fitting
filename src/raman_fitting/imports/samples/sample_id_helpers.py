from typing import Tuple, Optional, Dict
from pathlib import Path

from .models import SampleMetaData


def parse_string_to_sample_id_and_position(
    string: str, seps=("_", " ", "-")
) -> Tuple[str, int]:
    """
    Parser for the filenames -> finds SampleID and sample position

    Parameters
    ----------
    # ramanfile_string : str
    #    The filepath which the is parsed
    seps : tuple of str default
        ordered collection of seperators tried for split
        default : ('_', ' ', '-')

    Returns
    -------
    tuple of strings
        Collection of strings which contains the parsed elements.
    """

    split = None
    first_sep_match_index = min(
        [n for n, i in enumerate(seps) if i in string], default=None
    )
    first_sep_match = (
        seps[first_sep_match_index] if first_sep_match_index is not None else None
    )
    split = string.split(first_sep_match)
    _lensplit = len(split)

    position: int = 0
    sample_id: str = ""
    if _lensplit == 0:
        sample_id = split[0]
    elif len(split) == 1:
        sample_id = split[0]
    elif len(split) == 2:
        sample_id = split[0]
        _pos_strnum = "".join(i for i in split[1] if i.isnumeric())
        if _pos_strnum:
            position = int(_pos_strnum)
        else:
            try:
                position = int(split[1])
            except ValueError:
                pass
    elif len(split) >= 3:
        sample_id = "_".join(split[0:-1])
        _digits = "".join(filter(str.isdigit, split[-1]))
        if _digits:
            try:
                position = int(_digits)
            except ValueError:
                pass

    return (sample_id, position)


def extract_sample_group_from_sample_id(sample_id: str, max_len=4) -> str:
    """adding the extra sample Group key from sample ID"""

    _len = len(sample_id)
    _maxalphakey = min(
        [n for n, i in enumerate(sample_id) if not str(i).isalpha()], default=_len
    )
    _maxkey = min((_len, _maxalphakey, max_len))
    sample_group_id = "".join([i for i in sample_id[0:_maxkey] if i.isalpha()])
    return sample_group_id


def overwrite_sample_id_from_mapper(sample_id: str, mapper: dict) -> str:
    """Takes an sample_id and potentially overwrites from a mapper dict"""
    sample_id_map = mapper.get(sample_id)
    if sample_id_map is not None:
        return sample_id_map
    return sample_id


def overwrite_sample_group_id_from_parts(
    parts: list[str] | tuple[str, ...], sample_group_id: str, mapper: dict
) -> str:
    for k, val in mapper.items():
        if k in parts:
            sample_group_id = val
    return sample_group_id


def extract_sample_metadata_from_filepath(
    filepath: Path, sample_name_mapper: Optional[Dict[str, Dict[str, str]]] = None
) -> SampleMetaData:
    """parse the sample_id, position and sgrpID from stem"""
    stem = filepath.stem
    parts = filepath.parts

    sample_id, position = parse_string_to_sample_id_and_position(stem)

    if sample_name_mapper is not None:
        sample_id_mapper = sample_name_mapper.get("sample_id", {})
        sample_id = overwrite_sample_id_from_mapper(sample_id, sample_id_mapper)
    sample_group_id = extract_sample_group_from_sample_id(sample_id)

    if sample_name_mapper is not None:
        sample_grp_mapper = sample_name_mapper.get("sample_group_id", {})
        sample_group_id = overwrite_sample_group_id_from_parts(
            parts, sample_group_id, sample_grp_mapper
        )

    return SampleMetaData(id=sample_id, group=sample_group_id, position=position)
