from pathlib import Path
from typing import List, Collection, Tuple
import logging

from .models import RamanFileInfo

logger = logging.getLogger(__name__)


def collect_raman_file_infos(
    raman_files: Collection[Path],
) -> Tuple[List[RamanFileInfo], List[Path]]:
    pp_collection = []
    _files = []
    _failed_files = []
    for file in raman_files:
        _files.append(file)
        try:
            pp_res = RamanFileInfo(file=file)
            pp_collection.append(pp_res)
        except Exception as exc:
            logger.warning(
                f"{__name__} collect_raman_file_infos unexpected error for calling RamanFileInfo on\n{file}.\n{exc}"
            )
            _failed_files.append({"file": file, "error": exc})
    if _failed_files:
        logger.warning(
            f"{__name__} collect_raman_file_infos failed for {len(_failed_files)}."
        )

    return pp_collection, _files
