from typing import List

from raman_fitting.models.spectrum import SpectrumData


def raw_data_spectra_export(spectra: List[SpectrumData]):
    try:
        for spec in spectra:
            wnxl_outpath_spectra = spec.mean_info.DestRaw.unique()[0].joinpath(
                f"spectra_{spec.sIDmean_col}_{spec.regionname}.xlsx"
            )
            spec.mean_spec.to_excel(wnxl_outpath_spectra)

        _0_spec = spectra[0]
        wnxl_outpath_info = _0_spec.mean_info.DestRaw.unique()[0].joinpath(
            f"info_{_0_spec.sIDmean_col}.xlsx"
        )
        _0_spec.mean_info.to_excel(wnxl_outpath_info)
    except Exception as e:
        print("no extra Raw Data plots: {0}".format(e))


def export_xls_from_spec(self, res_peak_spec):
    try:
        res_peak_spec.FitComponents.to_excel(
            res_peak_spec.extrainfo["DestFittingModel"].with_suffix(".xlsx"),
            index=False,
        )

    except Exception as e:
        print("Error export_xls_from_spec", e)
