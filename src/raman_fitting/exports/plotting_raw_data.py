#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 14:49:50 2020

@author: DW
"""

from typing import Dict


import matplotlib
import matplotlib.pyplot as plt

from raman_fitting.exports.plot_formatting import get_plot_region_axes
from raman_fitting.models.deconvolution.spectrum_regions import SpectrumRegionLimits
from raman_fitting.models.spectrum import SpectrumData
from raman_fitting.models.splitter import RegionNames
from raman_fitting.config import settings
from raman_fitting.config.path_settings import (
    CLEAN_SPEC_REGION_NAME_PREFIX,
    ExportPathSettings,
)
from raman_fitting.delegators.models import AggregatedSampleSpectrumFitResult

from loguru import logger

from .models import ExportResultSet, ExportResult
from .plot_formatting import RAW_MEAN_SPEC_FMT, RAW_SOURCES_SPEC_FMT

matplotlib.rcParams.update({"font.size": 14})


def filter_regions_for_spectrum(
    regions: Dict[str, SpectrumRegionLimits], spectrum: SpectrumData
):
    ramanshift_min = spectrum.ramanshift.min()
    ramanshift_max = spectrum.ramanshift.max()
    valid_regions = {}
    for region_name, region in regions.items():
        if ramanshift_min > region.min:
            continue
        if ramanshift_max < region.max:
            continue
        valid_regions[region_name] = region
    return valid_regions


def raw_data_spectra_plot(
    aggregated_spectra: Dict[RegionNames, AggregatedSampleSpectrumFitResult],
    export_paths: ExportPathSettings,
) -> ExportResultSet:
    export_results = ExportResultSet()
    if not aggregated_spectra:
        return export_results

    sources = list(aggregated_spectra.values())[0].aggregated_spectrum.sources
    sample_id = "-".join(set(i.file_info.sample.id for i in sources))
    regions = settings.default_regions
    valid_regions = filter_regions_for_spectrum(regions, sources[0].read.spectrum)

    destfile = export_paths.plots.joinpath(f"{sample_id}_mean.png")
    destfile.parent.mkdir(exist_ok=True, parents=True)

    nrows = 3
    plot_region_axes = get_plot_region_axes(nrows=nrows, regions=valid_regions)
    _, ax = plt.subplots(2, nrows, figsize=(18, 12))

    for spec_source in sources:
        for (
            source_region_label,
            source_region,
        ) in spec_source.processed.clean_spectrum.spec_regions.items():
            _source_region_name = source_region.region_name.split(
                CLEAN_SPEC_REGION_NAME_PREFIX
            )[-1]
            if _source_region_name not in valid_regions:
                continue
            ax_ = ax[plot_region_axes[_source_region_name]]
            ax_.plot(
                source_region.ramanshift,
                source_region.intensity,
                label=f"{spec_source.file_info.file.stem}",
                **RAW_SOURCES_SPEC_FMT,
            )
            ax_.set_title(_source_region_name)
            if _source_region_name in aggregated_spectra:
                mean_spec = aggregated_spectra[
                    _source_region_name
                ].aggregated_spectrum.spectrum
                # plot the mean aggregated spectrum
                ax_.plot(
                    mean_spec.ramanshift,
                    mean_spec.intensity,
                    label=mean_spec.label,
                    **RAW_MEAN_SPEC_FMT,
                )

            # filter legend for a certain region
            ax_.legend(fontsize=10)

    plt.suptitle(f"Mean {sample_id}", fontsize=16)
    plt.savefig(
        destfile,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()
    _msg = f"raw_data_spectra_plot saved:\n{destfile}"
    logger.debug(_msg)
    _result = ExportResult(target=destfile, message=_msg)
    export_results.results.append(_result)
    return export_results
