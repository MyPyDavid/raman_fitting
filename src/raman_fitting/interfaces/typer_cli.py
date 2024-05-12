from typing import List, Optional
from typing_extensions import Annotated

from pathlib import Path
from enum import StrEnum, auto
from loguru import logger

from raman_fitting.config.load_config_from_toml import dump_default_config
from raman_fitting.config.path_settings import RunModes, INDEX_FILE_NAME
from raman_fitting.delegating.main_delegator import MainDelegator
from raman_fitting.imports.files.file_indexer import initialize_index_from_source_files
from raman_fitting.imports.spectrum.datafile_parsers import SPECTRUM_FILETYPE_PARSERS
from raman_fitting.models.deconvolution.spectrum_regions import RegionNames
from .utils import get_package_version

import typer


LOCAL_INDEX_FILE = Path.cwd().joinpath(INDEX_FILE_NAME)
LOCAL_CONFIG_FILE = Path.cwd().joinpath("raman_fitting.toml")


class MakeTypes(StrEnum):
    INDEX = auto()
    CONFIG = auto()
    EXAMPLE = auto()


class GenerateTypes(StrEnum):
    REGIONS = auto()
    MODELS = auto()
    PEAKS = auto()


__version__ = "0.1.0"


def version_callback(value: bool):
    if value:
        package_version = get_package_version()
        typer_cli_version = f"Awesome Typer CLI Version: {__version__}"
        print(f"{package_version}\n{typer_cli_version}")
        raise typer.Exit()


app = typer.Typer()
state = {"verbose": False}


def current_dir_prepare_index_kwargs():
    source_files = []
    for suffix in SPECTRUM_FILETYPE_PARSERS.keys():
        source_files += list(Path.cwd().rglob(f"*{suffix}"))
    index_file = LOCAL_INDEX_FILE
    force_reindex = True
    return source_files, index_file, force_reindex


@app.command()
def run(
    models: Annotated[
        List[str],
        typer.Option(
            default_factory=list, help="Selection of models to use for deconvolution."
        ),
    ],
    sample_ids: Annotated[
        List[str],
        typer.Option(
            default_factory=list,
            help="Selection of names of SampleIDs from index to run over.",
        ),
    ],
    group_ids: Annotated[
        List[str],
        typer.Option(
            default_factory=list,
            help="Selection of names of sample groups from index to run over.",
        ),
    ],
    fit_models: Annotated[
        List[str],
        typer.Option(
            default_factory=list,
            help="Selection of names of the Region that are to used for fitting.",
        ),
    ],
    run_mode: Annotated[RunModes, typer.Argument()] = RunModes.CURRENT_DIR,
    multiprocessing: Annotated[bool, typer.Option("--multiprocessing")] = False,
    index_file: Annotated[Path, typer.Option()] = None,
):
    if run_mode is None:
        print("No make run mode passed")
        raise typer.Exit()
    kwargs = {"run_mode": run_mode, "use_multiprocessing": multiprocessing}
    if run_mode == RunModes.CURRENT_DIR:
        source_files, index_file, force_reindex = current_dir_prepare_index_kwargs()
        initialize_index_from_source_files(
            files=source_files, index_file=index_file, force_reindex=force_reindex
        )
        kwargs.update({"index": index_file})
        dump_default_config(LOCAL_CONFIG_FILE)
        kwargs["use_multiprocessing"] = True
        fit_models = RegionNames
        # make index cwd
        # make config cwd
        # run fitting cwd
    elif run_mode == RunModes.EXAMPLES:
        kwargs.update(
            {
                "fit_model_specific_names": [
                    "2peaks",
                    "3peaks",
                    "4peaks",
                    "2nd_4peaks",
                ],
                "sample_groups": ["test"],
            }
        )

    if index_file is not None:
        index_file = Path(index_file).resolve()
        if not index_file.exists():
            raise FileNotFoundError(f"File does not exist. {index_file} ")
        kwargs.update({"index": index_file})
    if fit_models:
        kwargs.update({"fit_model_region_names": fit_models})
    if sample_ids:
        kwargs.update({"sample_ids": sample_ids})
    logger.info(f"Starting raman_fitting with CLI run mode: {run_mode}")
    logger.info(f"Starting raman_fitting with CLI kwargs: {kwargs}")
    _main_run = MainDelegator(**kwargs)


@app.command()
def make(
    make_type: Annotated[MakeTypes, typer.Argument()],
    source_files: Annotated[List[Path], typer.Option()] = None,
    index_file: Annotated[Path, typer.Option()] = None,
    force_reindex: Annotated[bool, typer.Option("--force-reindex")] = False,
):
    if make_type is None:
        print("No make type args passed")
        raise typer.Exit()
    if index_file:
        index_file = index_file.resolve()
    if make_type == MakeTypes.INDEX:
        if not source_files:
            source_files, index_file, force_reindex = current_dir_prepare_index_kwargs()
        initialize_index_from_source_files(
            files=source_files, index_file=index_file, force_reindex=force_reindex
        )
    elif make_type == MakeTypes.CONFIG:
        dump_default_config(LOCAL_CONFIG_FILE)


@app.command()
def generate(
    generate_type: Annotated[MakeTypes, typer.Argument()],
):
    """generate things in local cwd"""
    if generate_type == "peaks":
        pass


@app.callback()
def main(
    verbose: bool = False,
    version: Annotated[
        Optional[bool], typer.Option("--version", callback=version_callback)
    ] = None,
):
    """
    Manage raman_fitting in the awesome CLI app.
    """
    if verbose:
        print("Will write verbose output")
        state["verbose"] = True


if __name__ == "__main__":
    app()
