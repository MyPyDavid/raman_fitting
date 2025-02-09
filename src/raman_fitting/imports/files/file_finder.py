from pathlib import Path
from pydantic import BaseModel, DirectoryPath, Field, computed_field

from loguru import logger


class FileFinder(BaseModel):
    directory: DirectoryPath
    suffixes: list[str] = Field(default_factory=lambda: [".txt"])
    exclusions: list[str] = Field(default_factory=lambda: ["."])

    @computed_field
    @property
    def files(self) -> list[Path]:
        files = find_files(self.directory, self.suffixes, self.exclusions)
        if not files:
            logger.warning(
                f"FileFinder warning: no files were found in the chosen data file dir.\n{self.directory}\nPlease choose another directory which contains your data files."
            )
        return files


def find_files(
    directory: Path, suffixes: list[str], exclusions: list[str]
) -> list[Path]:
    """Find files in the directory with given suffixes and exclude paths containing any of the exclusions."""
    raman_files = []
    for suffix in suffixes:
        files = list(directory.rglob(f"**/*{suffix}"))
        if not files:
            logger.debug(
                f"find_files warning: no files were found for the suffix {suffix} in the chosen data file dir.\n{directory}\nPlease choose another directory which contains your data files."
            )
        else:
            logger.info(
                f"find_files {len(files)} files were found for the suffix {suffix} in the chosen data dir:\n\t{directory}"
            )
        raman_files += files

    if not raman_files:
        logger.debug(
            f"find_files warning: no files were found in the chosen data file dir.\n{directory}\nPlease choose another directory which contains your data files."
        )

    # Filter out files that have any Path.parts that start with an exclusion
    filtered_files = [
        file
        for file in raman_files
        if not any(
            part.startswith(exclusion)
            for part in file.parts
            for exclusion in exclusions
        )
    ]

    if raman_files and not filtered_files:
        logger.warning(
            f"find_files warning: the files were excluded because they contain the following exclusions:\n\t{exclusions}"
        )
    logger.info(
        f"find_files {len(filtered_files)} files were found in the chosen data dir:\n\t{directory}"
    )
    return filtered_files
