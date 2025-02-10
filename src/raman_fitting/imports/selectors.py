from typing import Sequence

from raman_fitting.imports.files.file_indexer import IndexSelector, RamanFileIndex
from raman_fitting.imports.models import RamanFileInfo

from loguru import logger


def select_samples_from_index(
    index: RamanFileIndex,
    select_sample_groups: Sequence[str],
    select_sample_ids: Sequence[str],
) -> Sequence[RamanFileInfo]:
    if index is None:
        raise ValueError("Index was not initialized")
    elif not index.raman_files:
        raise ValueError("Index file is empty.")

    index_selector = IndexSelector(
        raman_files=index.raman_files,
        sample_groups=select_sample_groups,
        sample_ids=select_sample_ids,
    )
    selection = index_selector.selection
    if not selection:
        logger.info("Selection was empty.")
    return selection
