import math

import pytest

from raman_fitting.models.fit_models import SpectrumFitModel
from raman_fitting.imports.spectrumdata_parser import SpectrumReader
from raman_fitting.processing.post_processing import SpectrumProcessor


@pytest.fixture
def clean_spec(example_files, default_regions) -> None:
    file = [i for i in example_files if "_pos4" in i.stem][0]
    specread = SpectrumReader(file)

    spectrum_processor = SpectrumProcessor(
        spectrum=specread.spectrum, region_limits=default_regions
    )
    clean_spec_1st_order = spectrum_processor.clean_spectrum.spec_regions[
        "savgol_filter_raw_region_first_order"
    ]
    clean_spec_1st_order.region_name = "first_order"
    return clean_spec_1st_order


def test_fit_first_order(clean_spec, default_models):
    spectrum = clean_spec
    test_component = "center"
    for model_name, test_model in default_models["first_order"].items():
        # with subTest(model_name=model_name, test_model=test_model):
        spec_fit = SpectrumFitModel(
            **{"spectrum": spectrum, "model": test_model, "region": "first_order"}
        )
        spec_fit.run_fit()
        for component in test_model.lmfit_model.components:
            # with subTest(component=component):
            peak_component = f"{component.prefix}{test_component}"
            fit_value = spec_fit.fit_result.best_values[peak_component]
            init_value = spec_fit.fit_result.init_values[peak_component]
            assert math.isclose(fit_value, init_value, rel_tol=0.05)
            assert spec_fit.fit_result.success
