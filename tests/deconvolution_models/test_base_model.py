"""
Created on Sun Jun  6 09:35:02 2021

@author: DW
"""

import pytest
from functools import partial

from pydantic import ValidationError

from raman_fitting.models.deconvolution.base_model import (
    BaseLMFitModel,
)

SI_SUBSTRATE_PEAK = "Si1_peak"
SI_SUBSTRATE_PREFIX = SI_SUBSTRATE_PEAK.split("peak")[0]


def helper_get_list_components(bm):
    _listcompsprefix = partial(map, lambda x,: getattr(x, "prefix"))
    _bm_prefix = list(_listcompsprefix(bm.lmfit_model.components))
    return _bm_prefix


def test_empty_base_model():
    with pytest.raises(ValidationError):
        BaseLMFitModel()
    with pytest.raises(ValidationError):
        BaseLMFitModel(name="Test_empty")

    with pytest.raises(ValidationError):
        BaseLMFitModel(peaks="A+B")


@pytest.mark.skip("raise validationerror")
def test_empty_base_model_missing_peak():
    # breakpoint()
    with pytest.raises(ValidationError):
        BaseLMFitModel(name="Test_empty", peaks="A+B", region_name="full")


def test_base_model_2peaks():
    # breakpoint()
    bm = BaseLMFitModel(name="Test_2peaks", peaks="K2+D+G", region_name="full")
    assert set(helper_get_list_components(bm)) == set(["D_", "G_"])
    bm.add_substrate()
    assert SI_SUBSTRATE_PREFIX in set(helper_get_list_components(bm))
    # == set(["D_", "G_", SUBSTRATE_PREFIX]))
    bm.remove_substrate()
    assert set(helper_get_list_components(bm)) == set(["D_", "G_"])


def test_base_model_wrong_chars_model_name():
    bm = BaseLMFitModel(
        name="Test_wrong_chars",
        peaks="K2+---////+  +7 +K1111+1D+D2",
        region_name="full",
    )
    assert set(helper_get_list_components(bm)) == set(["D2_"])
    bm.add_substrate()
    assert SI_SUBSTRATE_PREFIX in set(helper_get_list_components(bm))
