import pytest

from raman_fitting.imports.models import RamanFileInfo
from raman_fitting.imports.samples.sample_id_helpers import (
    overwrite_sample_id_from_mapper,
    overwrite_sample_group_id_from_parts,
)


from raman_fitting.imports.samples.sample_id_helpers import (
    parse_string_to_sample_id_and_position,
)

example_parse_fixture = {
    "errEMP2_1.txt": ("errEMP2", 1),
    "errTS2_pos1.txt": ("errTS2", 1),
    "Si_spectrum01.txt": ("Si", 1),
    "testDW38C_pos1.txt": ("testDW38C", 1),
    "testDW38C_pos2.txt": ("testDW38C", 2),
    "testDW38C_pos3.txt": ("testDW38C", 3),
    "testDW38C_pos4.txt": ("testDW38C", 4),
    "DW_AB_CD-EF_GE_pos3": ("DW_AB_CD-EF_GE", 3),
    "DW99-pos3": ("DW99", 3),
    "Si": ("Si", 0),
}


# class TestFilenameParser(unittest.TestCase):
result_attr = "parse_result"
sample_id_name_mapper = {}
sGrp_name_mapper = {}


@pytest.fixture()
def path_parsers(example_files):
    path_parsers_ = []
    for fn in example_files:
        path_parsers_.append(RamanFileInfo(file=fn))
    return path_parsers_


def test_ramanfileinfo(path_parsers):
    assert all(isinstance(i, RamanFileInfo) for i in path_parsers)


def test_sample_id_name_mapper():
    for k, val in sample_id_name_mapper.items():
        _mapval = overwrite_sample_id_from_mapper(k, sample_id_name_mapper)
        assert _mapval == val


def test_overwrite_sample_id_from_mapper():
    assert "TEST" == overwrite_sample_group_id_from_parts([], "TEST", sGrp_name_mapper)
    for k, val in sGrp_name_mapper.items():
        empty_path_parts = RamanFileInfo(file=f"{k}/TEST.txt")
        assert val == overwrite_sample_group_id_from_parts(
            empty_path_parts.parts, "TEST", sGrp_name_mapper
        )


def test_parse_string_to_sample_id_and_position():
    for file, _expected in example_parse_fixture.items():
        assert parse_string_to_sample_id_and_position(file) == _expected
