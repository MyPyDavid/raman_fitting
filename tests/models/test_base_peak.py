from raman_fitting.models.deconvolution.base_peak import BasePeak


def test_initialize_base_peaks(
    default_definitions, default_models_first_order, default_models_second_order
):
    peaks = {}
    region_definitions = default_definitions["spectrum"]["regions"]
    peak_items = {
        **region_definitions["first_order"]["peaks"],
        **region_definitions["second_order"]["peaks"],
    }.items()
    for k, v in peak_items:
        peaks.update({k: BasePeak(**v)})

    peak_d = BasePeak(**region_definitions["first_order"]["peaks"]["D"])
    assert (
        peak_d.peak_name == region_definitions["first_order"]["peaks"]["D"]["peak_name"]
    )
    assert (
        peak_d.peak_type == region_definitions["first_order"]["peaks"]["D"]["peak_type"]
    )
    assert (
        peak_d.lmfit_model.components[0].prefix
        == region_definitions["first_order"]["peaks"]["D"]["peak_name"] + "_"
    )
    assert (
        peak_d.param_hints["center"].value
        == region_definitions["first_order"]["peaks"]["D"]["param_hints"]["center"][
            "value"
        ]
    )
