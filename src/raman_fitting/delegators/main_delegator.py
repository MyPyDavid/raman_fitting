# pylint: disable=W0614,W0401,W0611,W0622,C0103,E0401,E0402
from dataclasses import dataclass, field
from typing import Sequence, Dict, Any, List

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

from raman_fitting.delegators.models import (
    AggregatedSampleSpectrumFitResult,
)
from raman_fitting.delegators.pre_processing import (
    prepare_aggregated_spectrum_from_files,
)
from raman_fitting.models.deconvolution.base_model import LMFitModelCollection
from raman_fitting.delegators.run_fit_spectrum import run_fit_over_selected_models

from loguru import logger


@dataclass
class MainDelegator:
    """
    Main delegator for processing files containing Raman spectra.

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
    suffixes: List[str] = field(default_factory=lambda: [".txt"])
    exclusions: List[str] = field(default_factory=lambda: ["."])
    export: bool = True
    results: Dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.index = initialize_index(
            self.index,
            self.exclusions,
            self.suffixes,
            self.run_mode_paths,
        )
        if not self.index:
            logger.info("Index is empty.")
            return
        self.selection = initialize_selection(
            self.index, self.select_sample_groups, self.select_sample_ids
        )
        self.selected_models = initialize_models(
            self.fit_model_region_names,
            self.fit_model_specific_names,
            self.lmfit_models,
        )
        self.results = main_run(
            self.index,
            self.select_sample_groups,
            self.select_sample_ids,
            self.run_mode_paths,
            self.selected_models,
            self.use_multiprocessing,
            self.fit_model_region_names,
        )
        if self.export:
            call_export_manager(
                self.run_mode,
                self.results,
            )

    @property
    def run_mode_paths(self) -> RunModePaths | None:
        if not self.run_mode:
            return None
        return initialize_run_mode_paths(self.run_mode)

    def select_fitting_model(
        self, region_name: RegionNames, model_name: str
    ) -> BaseLMFitModel:
        try:
            return self.lmfit_models[region_name][model_name]
        except KeyError as exc:
            raise KeyError(f"Model {region_name} {model_name} not found.") from exc


def main_run(
    index: RamanFileIndex,
    select_sample_groups: Sequence[str],
    select_sample_ids: Sequence[str],
    run_mode_paths: RunModePaths,
    selected_models: LMFitModelCollection,
    use_multiprocessing: bool,
    fit_model_region_names: Sequence[RegionNames],
) -> Dict[str, Any] | None:
    try:
        selection = select_samples_from_index(
            index, select_sample_groups, select_sample_ids
        )
        logger.debug(f"Selected {len(selection)} samples.")
    except ValueError as exc:
        logger.error(f"Selection failed. {exc}")
        return {}

    if not fit_model_region_names:
        logger.info("No model region names were selected.")
    if not selected_models:
        logger.info("No fit models were selected.")

    results = process_selection(
        selection, selected_models, use_multiprocessing, run_mode_paths
    )
    log_results(results)
    return results


def log_results(results) -> None:
    if results:
        logger.debug("Results: {}", results)
    else:
        logger.warning("No results generated.")


def initialize_index(
    index: RamanFileIndex | FilePath | None = None,
    exclusions: Sequence[str] = (),
    suffixes: Sequence[str] = (),
    run_mode_paths: RunModePaths | None = None,
    force_reindex: bool = False,
    persist_index: bool = False,
) -> RamanFileIndex:
    if isinstance(index, RamanFileIndex):
        return index

    if run_mode_paths is None:
        raise ValueError("Run mode paths are not initialized.")
    else:
        index = get_or_create_index(
            index,
            directory=run_mode_paths.dataset_dir,
            suffixes=suffixes,
            exclusions=exclusions,
            index_file=run_mode_paths.index_file,
            force_reindex=force_reindex,
            persist_index=persist_index,
        )

    return index


def initialize_selection(
    index: RamanFileIndex,
    select_sample_groups: Sequence[str],
    select_sample_ids: Sequence[str],
) -> Sequence[RamanFileInfo]:
    return select_samples_from_index(index, select_sample_groups, select_sample_ids)


def initialize_models(
    region_names: Sequence[RegionNames],
    model_names: Sequence[str],
    provided_models: LMFitModelCollection,
) -> LMFitModelCollection:
    return select_models_from_provided_models(
        region_names=region_names,
        model_names=model_names,
        provided_models=provided_models,
    )


def process_selection(
    selection: Sequence[RamanFileInfo],
    selected_models: LMFitModelCollection,
    use_multiprocessing: bool,
    run_mode_paths: RunModePaths,
) -> Dict[str, Any]:
    results = {}
    for group_name, grp in group_by_sample_group(selection):
        results[group_name] = process_group(
            group_name, grp, selected_models, use_multiprocessing, run_mode_paths
        )
    return results


def process_group(
    group_name: str,
    grp: Sequence[RamanFileInfo],
    selected_models: LMFitModelCollection,
    use_multiprocessing: bool,
    run_mode_paths: RunModePaths,
) -> Dict[str, Any]:
    results = {}
    for sample_id, sample_id_grp in group_by_sample_id(grp):
        results[sample_id] = process_sample(
            group_name,
            sample_id,
            sample_id_grp,
            selected_models,
            use_multiprocessing,
            run_mode_paths,
        )
    return results


def process_sample(
    group_name: str,
    sample_id: str,
    sample_id_grp: Sequence[RamanFileInfo],
    selected_models: LMFitModelCollection,
    use_multiprocessing: bool,
    run_mode_paths: RunModePaths,
) -> Dict[str, Any]:
    if not sample_id_grp:
        _error_msg = ERROR_MSG_TEMPLATE.format(group_name, sample_id, "group is empty")
        logger.debug(_error_msg)
        return {"errors": _error_msg}

    sample_id_grp = sorted(sample_id_grp, key=lambda x: x.sample.position)
    unique_positions = {i.sample.position for i in sample_id_grp}

    if len(unique_positions) < len(sample_id_grp):
        _error_msg = f"Handle multiple source files for a single position on a sample, {group_name} {sample_id}"
        logger.debug(_error_msg)
        return {"errors": _error_msg}

    model_result = run_fit_over_selected_models(
        sample_id_grp,
        selected_models,
        use_multiprocessing=use_multiprocessing,
        file_paths=run_mode_paths,
    )
    return {"fit_results": model_result}


def get_results_over_selected_models(
    raman_files: List[RamanFileInfo],
    models: LMFitModelCollection,
    fit_model_results: Dict[str, Any],
) -> Dict[RegionNames, AggregatedSampleSpectrumFitResult]:
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


def call_export_manager(run_mode, results) -> List[Dict[str, Any]]:
    export_manager = ExportManager(run_mode, results)
    return export_manager.export_files()


def make_examples(**kwargs) -> MainDelegator:
    _main_run = MainDelegator(
        run_mode=RunModes.PYTEST,
        fit_model_specific_names=["2peaks", "2nd_4peaks"],
        export=False,
        **kwargs,
    )
    assert isinstance(_main_run.index, RamanFileIndex)
    assert isinstance(_main_run.run_mode_paths, RunModePaths)
    main_run(
        _main_run.index,
        _main_run.select_sample_groups,
        _main_run.select_sample_ids,
        _main_run.run_mode_paths,
        _main_run.selected_models,
        _main_run.use_multiprocessing,
        _main_run.fit_model_region_names,
    )
    return _main_run


if __name__ == "__main__":
    example_run = make_examples()
