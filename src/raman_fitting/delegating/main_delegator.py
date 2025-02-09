# pylint: disable=W0614,W0401,W0611,W0622,C0103,E0401,E0402
from dataclasses import dataclass, field
from typing import Sequence, Any

from pydantic import FilePath

from raman_fitting.config.path_settings import (
    RunModes,
    ERROR_MSG_TEMPLATE,
    initialize_run_mode_paths,
    RunModePaths,
)
from raman_fitting.config import settings

from raman_fitting.imports.models import RamanFileInfo
from raman_fitting.imports.selectors import select_samples_from_index

from raman_fitting.models.deconvolution.base_model import BaseLMFitModel
from raman_fitting.models.selectors import select_models_from_provided_models
from raman_fitting.models.splitter import RegionNames
from raman_fitting.exports.exporter import ExportManager
from raman_fitting.imports.files.file_indexer import (
    RamanFileIndex,
    group_by_sample_group,
    group_by_sample_id,
    get_or_create_index,
)

from raman_fitting.delegating.models import (
    AggregatedSampleSpectrumFitResult,
)
from raman_fitting.delegating.pre_processing import (
    prepare_aggregated_spectrum_from_files,
)
from raman_fitting.models.deconvolution.base_model import LMFitModelCollection
from raman_fitting.delegating.run_fit_spectrum import run_fit_over_selected_models


from loguru import logger


@dataclass
class MainDelegator:
    # IDEA Add flexible input handling for the cli, such a path to dir, or list of files
    #  or create index when no kwargs are given.
    """
    Main delegator for the processing of files containing Raman spectra.

    Creates plots and files in the config RESULTS directory.
    """

    run_mode: RunModes | None = field(default=None)
    use_multiprocessing: bool = field(default=False, repr=False)
    lmfit_models: LMFitModelCollection = field(
        default_factory=lambda: settings.default_models,
        repr=False,
    )
    fit_model_region_names: Sequence[RegionNames] = field(
        default=(RegionNames.FIRST_ORDER, RegionNames.SECOND_ORDER)
    )
    fit_model_specific_names: Sequence[str] | None = None
    select_sample_ids: Sequence[str] = field(default_factory=list)
    select_sample_groups: Sequence[str] = field(default_factory=list)
    index: RamanFileIndex | FilePath | None = field(default=None, repr=False)
    selection: Sequence[RamanFileInfo] = field(init=False)
    selected_models: Sequence[RamanFileInfo] = field(init=False)

    results: dict[str, Any] | None = field(default=None, init=False, repr=False)
    export: bool = True
    suffixes: list[str] = field(default_factory=lambda: [".txt"])
    exclusions: list[str] = field(default_factory=lambda: ["."])

    def __post_init__(self):
        self.index = get_or_create_index(
            self.index,
            directory=self.run_mode_paths.dataset_dir,
            suffixes=self.suffixes,
            exclusions=self.exclusions,
            index_file=self.run_mode_paths.index_file,
            force_reindex=False,
            persist_index=False,
        )
        if len(self.index) == 0:
            logger.info("Index is empty.")
            return

        self.selection = select_samples_from_index(
            self.index, self.select_sample_groups, self.select_sample_ids
        )
        self.selected_models = select_models_from_provided_models(
            region_names=self.fit_model_region_names,
            model_names=self.fit_model_specific_names,
            provided_models=self.lmfit_models,
        )

        self.main_run()
        if self.export:
            self.exports = self.call_export_manager()

    def call_export_manager(self):
        export = ExportManager(self.run_mode, self.results)
        exports = export.export_files()
        return exports

    @property
    def run_mode_paths(self) -> RunModePaths:
        return initialize_run_mode_paths(self.run_mode)

    # region_names:list[RegionNames], model_names: list[str]
    def select_fitting_model(
        self, region_name: RegionNames, model_name: str
    ) -> BaseLMFitModel:
        try:
            return self.lmfit_models[region_name][model_name]
        except KeyError as exc:
            raise KeyError(f"Model {region_name} {model_name} not found.") from exc

    def main_run(self):
        try:
            selection = select_samples_from_index(
                self.index, self.select_sample_groups, self.select_sample_ids
            )
        except ValueError as exc:
            logger.error(f"Selection failed. {exc}")
            return

        if not self.fit_model_region_names:
            logger.info("No model region names were selected.")
        if not self.selected_models:
            logger.info("No fit models were selected.")

        results = {}

        for group_name, grp in group_by_sample_group(selection):
            results[group_name] = {}
            for sample_id, sample_grp in group_by_sample_id(grp):
                sgrp = list(sample_grp)
                results[group_name][sample_id] = {}
                _error_msg = None

                if not sgrp:
                    _err = "group is empty"
                    _error_msg = ERROR_MSG_TEMPLATE.format(group_name, sample_id, _err)
                    logger.debug(_error_msg)
                    results[group_name][sample_id]["errors"] = _error_msg
                    continue

                unique_positions = {i.sample.position for i in sgrp}
                if len(unique_positions) <= len(sgrp):
                    #  handle edge-case, multiple source files for a single position on a sample
                    _error_msg = f"Handle multiple source files for a single position on a sample, {group_name} {sample_id}"
                    results[group_name][sample_id]["errors"] = _error_msg
                    logger.debug(_error_msg)
                model_result = run_fit_over_selected_models(
                    sgrp,
                    self.selected_models,
                    use_multiprocessing=self.use_multiprocessing,
                    file_paths=self.run_mode_paths,
                )
                results[group_name][sample_id]["fit_results"] = model_result
        self.results = results


def get_results_over_selected_models(
    raman_files: list[RamanFileInfo], models: LMFitModelCollection, fit_model_results
) -> dict[RegionNames, AggregatedSampleSpectrumFitResult]:
    results = {}
    for region_name, region_grp in models.items():
        try:
            region_name = RegionNames(region_name)
        except ValueError as exc:
            logger.error(f"Region name {region_name} not found. {exc}")
            continue

        aggregated_spectrum = prepare_aggregated_spectrum_from_files(
            region_name, raman_files
        )
        if aggregated_spectrum is None:
            continue
        fit_region_results = AggregatedSampleSpectrumFitResult(
            region_name=region_name,
            aggregated_spectrum=aggregated_spectrum,
            fit_model_results=fit_model_results,
        )
        results[region_name] = fit_region_results
    return results


def make_examples(**kwargs):
    # breakpoint()
    _main_run = MainDelegator(
        run_mode=RunModes.PYTEST,
        fit_model_specific_names=["2peaks", "2nd_4peaks"],
        export=False,
        **kwargs,
    )
    _main_run.main_run()
    return _main_run


if __name__ == "__main__":
    example_run = make_examples()
