"""Indexer for raman data files"""

from itertools import groupby
from pathlib import Path
from typing import List, Sequence, TypeAlias

from loguru import logger
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    NewPath,
    model_validator,
)
from raman_fitting.config import settings
from raman_fitting.imports.collector import collect_raman_file_infos
from raman_fitting.imports.files.utils import (
    load_dataset_from_file,
    write_dataset_to_file,
)
from raman_fitting.imports.models import RamanFileInfo
from tablib import Dataset

from raman_fitting.imports.spectrum.datafile_parsers import SPECTRUM_FILETYPE_PARSERS

RamanFileInfoSet: TypeAlias = Sequence[RamanFileInfo]


class RamanFileIndex(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    index_file: NewPath | FilePath | None = Field(None, validate_default=False)
    raman_files: RamanFileInfoSet | None = Field(None)
    dataset: Dataset | None = Field(None)
    force_reindex: bool = Field(False, validate_default=False)
    persist_to_file: bool = Field(True, validate_default=False)

    @model_validator(mode="after")
    def read_or_load_data(self) -> "RamanFileIndex":
        if not any([self.index_file, self.raman_files, self.dataset]):
            raise ValueError("Not all fields should be empty.")

        reload_from_file = validate_reload_from_index_file(
            self.index_file, self.force_reindex
        )
        if reload_from_file:
            self.dataset = load_dataset_from_file(self.index_file)
            if not self.raman_files and self.dataset:
                self.raman_files = parse_dataset_to_index(self.dataset)
                return self

        if self.raman_files is not None:
            dataset_rf = cast_raman_files_to_dataset(self.raman_files)
            if self.dataset is not None:
                assert (
                    dataset_rf == self.dataset
                ), "Both dataset and raman_files provided and they are different."
            self.dataset = dataset_rf

        if self.dataset is not None:
            self.raman_files = parse_dataset_to_index(self.dataset)

        if self.raman_files is None and self.dataset is None:
            raise ValueError(
                "Index error, both raman_files and dataset are not provided."
            )

        if self.persist_to_file and self.index_file is not None:
            write_dataset_to_file(self.index_file, self.dataset)

        return self


def validate_reload_from_index_file(
    index_file: Path | None, force_reindex: bool
) -> bool:
    if index_file is None:
        logger.debug(
            "Index file not provided, index will not be reloaded or persisted."
        )
        return False
    if index_file.exists() and not force_reindex:
        return True
    elif force_reindex:
        logger.warning(
            f"Index index_file file {index_file} exists and will be overwritten."
        )
    else:
        logger.info(
            "Index index_file file does not exists but was asked to reload from it."
        )
    return False


def cast_raman_files_to_dataset(raman_files: RamanFileInfoSet) -> Dataset:
    headers = list(RamanFileInfo.model_fields.keys())
    data = Dataset(headers=headers)
    for file in raman_files:
        data.append(file.model_dump(mode="json").values())
    return data


def parse_dataset_to_index(dataset: Dataset) -> RamanFileInfoSet:
    raman_files = []
    for row in dataset:
        row_data = dict(zip(dataset.headers, row))
        raman_files.append(RamanFileInfo(**row_data))
    return raman_files


class IndexSelector(BaseModel):
    raman_files: Sequence[RamanFileInfo]
    sample_ids: List[str] = Field(default_factory=list)
    sample_groups: List[str] = Field(default_factory=list)
    selection: Sequence[RamanFileInfo] = Field(default_factory=list)

    @model_validator(mode="after")
    def make_and_set_selection(self) -> "IndexSelector":
        rf_index = self.raman_files
        if not any([self.sample_groups, self.sample_ids]):
            self.selection = rf_index
            logger.debug(
                f"{self.__class__.__qualname__} did not get any query parameters, selected {len(self.selection)} of {len(rf_index)}. "
            )
            return self

        _pre_selected_samples = {i.sample.id for i in rf_index}
        rf_selection_index = []
        if self.sample_groups:
            rf_index_groups = list(
                filter(lambda x: x.sample.group in self.sample_groups, rf_index)
            )
            _pre_selected_samples = {i.sample.id for i in rf_index_groups}
            rf_selection_index += rf_index_groups

        if self.sample_ids:
            selected_sample_ids = list(
                filter(lambda x: x in self.sample_ids, _pre_selected_samples)
            )
            rf_index_samples = list(
                filter(lambda x: x.sample.id in selected_sample_ids, rf_index)
            )
            rf_selection_index += rf_index_samples
        self.selection = rf_selection_index
        logger.debug(
            f"{self.__class__.__qualname__} selected {len(self.selection)} of {len(rf_index)}. "
        )
        return self


def groupby_sample_group(index: RamanFileInfoSet):
    """Generator for Sample Groups, yields the name of group and group of the index SampleGroup"""
    grouper = groupby(index, key=lambda x: x.sample.group)
    return grouper


def groupby_sample_id(index: RamanFileInfoSet):
    """Generator for SampleIDs, yields the name of group, name of SampleID and group of the index of the SampleID"""
    grouper = groupby(index, key=lambda x: x.sample.id)
    return grouper


def iterate_over_groups_and_sample_id(index: RamanFileInfoSet):
    for grp_name, grp in groupby_sample_group(index):
        for sample_id, sgrp in groupby_sample_group(grp):
            yield grp_name, grp, sample_id, sgrp


def select_index_by_sample_groups(index: RamanFileInfoSet, sample_groups: List[str]):
    return filter(lambda x: x.sample.group in sample_groups, index)


def select_index_by_sample_ids(index: RamanFileInfoSet, sample_ids: List[str]):
    return filter(lambda x: x.sample.id in sample_ids, index)


def select_index(
    index: RamanFileInfoSet, sample_groups: List[str], sample_ids: List[str]
):
    group_selection = list(select_index_by_sample_groups(index, sample_groups))
    sample_selection = list(select_index_by_sample_ids(index, sample_ids))
    selection = group_selection + sample_selection
    return selection


def collect_raman_file_index_info(
    raman_files: Sequence[Path] | None = None, **kwargs
) -> RamanFileInfoSet | None:
    """loops over the files and scrapes the index data from each file"""
    if raman_files is None:
        return
    raman_files = list(raman_files)
    dirs, files, total_files = [], [], []
    for f in raman_files:
        f_ = f.resolve()
        if f_.is_dir():
            dirs.append(f_)
        elif f_.is_file():
            files.append(f_)
    total_files += files
    suffixes = [i.lstrip(".") for i in SPECTRUM_FILETYPE_PARSERS.keys()]
    for d1 in dirs:
        paths = [path for i in suffixes for path in d1.rglob(f"*.{i}")]
        total_files += paths
    index, files = collect_raman_file_infos(total_files, **kwargs)
    logger.info(f"successfully made index {len(index)} from {len(files)} files")
    return index


def initialize_index_from_source_files(
    files: Sequence[Path] | None = None,
    index_file: Path | None = None,
    force_reindex: bool = False,
) -> RamanFileIndex:
    raman_files = collect_raman_file_index_info(raman_files=files)
    # breakpoint()
    raman_index = RamanFileIndex(
        index_file=index_file, raman_files=raman_files, force_reindex=force_reindex
    )
    logger.info(
        f"index_delegator index prepared with len {len(raman_index.raman_files)}"
    )
    return raman_index


def main():
    """test run for indexer"""
    index_file = settings.destination_dir.joinpath("index.csv")
    raman_files = collect_raman_file_index_info()
    try:
        index_data = {"file": index_file, "raman_files": raman_files}
        raman_index = RamanFileIndex(**index_data)
        logger.debug(f"Raman Index len: {len(raman_index.dataset)}")
        select_index(raman_index.raman_files, sample_groups=["DW"], sample_ids=["DW38"])
    except Exception as e:
        logger.error(f"Raman Index error: {e}")
        raman_index = None

    return raman_index


if __name__ == "__main__":
    main()
