import sys
from typing import List, Optional
from typing_extensions import Annotated
from pathlib import Path
from enum import StrEnum, auto

from raman_fitting.config.load_config_from_toml import dump_default_config
from raman_fitting.config.path_settings import RunModes, INDEX_FILE_NAME
from raman_fitting.delegators.main_delegator import MainDelegator
from raman_fitting.imports.files.file_finder import FileFinder
from raman_fitting.imports.files.file_indexer import initialize_index_from_source_files
from raman_fitting.imports.spectrum.datafile_parsers import SPECTRUM_FILETYPE_PARSERS
from raman_fitting.models.deconvolution.spectrum_regions import RegionNames
from .utils import get_package_version

from rich.console import Console
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


console = Console()

app = typer.Typer()
state = {"verbose": False}


def current_dir_prepare_index_kwargs():
    file_finder = FileFinder(
        directory=Path.cwd(),
        suffixes=SPECTRUM_FILETYPE_PARSERS.keys(),
        exclusions=["."],
    )
    source_files = file_finder.files
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
    index_file: Annotated[Optional[Path], typer.Option()] = None,
    log_file: Annotated[Optional[Path], typer.Option("--log-file")] = None,
    log_level: Annotated[str, typer.Option("--log-level")] = "INFO",
):
    run_mode = RunModes(run_mode)

    kwargs = {"run_mode": run_mode, "use_multiprocessing": multiprocessing}
    if run_mode == RunModes.CURRENT_DIR:
        source_files, index_file, force_reindex = current_dir_prepare_index_kwargs()
        raman_index = initialize_index_from_source_files(
            files=source_files, index_file=index_file, force_reindex=force_reindex
        )
        if not raman_index.dataset:
            console.print(
                f"No Raman files could be indexed in {Path.cwd()}", style="bold red"
            )
            typer.Exit(code=1)

        kwargs.update({"index": index_file})
        # make config cwd
        dump_default_config(LOCAL_CONFIG_FILE)
        fit_models = RegionNames
        # make index cwd
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
                "select_sample_groups": ["test"],
            }
        )

    if index_file is not None:
        index_file = Path(index_file).resolve()
        if not index_file.exists():
            console.print(
                f"Index file does not exist but is required. {index_file}",
                style="bold red",
            )
            typer.Exit(code=1)

        kwargs.update({"index": index_file})
    if fit_models:
        kwargs.update({"fit_model_region_names": fit_models})
    if sample_ids:
        kwargs.update({"select_sample_ids": sample_ids})
    if group_ids:
        kwargs.update({"select_sample_groups": group_ids})

    from loguru import logger

    logger.enable("raman_fitting")
    # Set the log level
    logger.remove()  # Remove any existing handlers
    logger.add(sys.stderr, level=log_level)

    # Configure the logger to write to the specified log file if provided
    if log_file:
        log_file = Path(log_file).resolve()
        logger.add(log_file, level=log_level, rotation="10 MB")

    console.print(
        f"Starting raman_fitting with CLI run mode: {run_mode}\nand kwargs: {kwargs}"
    )
    _main_run = MainDelegator(**kwargs)
    logger.disable("raman_fitting")


@app.command()
def make(
    make_type: Annotated[MakeTypes, typer.Argument()],
    source_files: Annotated[List[Path] | None, typer.Option()] = None,
    index_file: Annotated[Path | None, typer.Option()] = None,
    force_reindex: Annotated[bool, typer.Option("--force-reindex")] = False,
):
    if make_type == MakeTypes.INDEX:
        if index_file is not None:
            index_file = index_file.resolve()

        if not source_files:
            source_files, index_file, force_reindex = current_dir_prepare_index_kwargs()
        index = initialize_index_from_source_files(
            files=source_files,
            index_file=index_file,
            force_reindex=force_reindex,
            persist_to_file=True,
        )
        if index is not None:
            typer.echo(f"index prepared and saved to {index.index_file}")
    elif make_type == MakeTypes.CONFIG:
        dump_default_config(LOCAL_CONFIG_FILE)
        typer.echo(f"config file created: {LOCAL_CONFIG_FILE}")


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
