"""this module prepares the local file paths for data and results"""

from pathlib import Path

from loguru import logger


def check_and_make_dirs(destdir: Path) -> None:
    _destfile = None
    if destdir.suffix:
        _destfile = destdir
        destdir = _destfile.parent

    if not destdir.is_dir():
        destdir.mkdir(exist_ok=True, parents=True)
        logger.info(
            f"check_and_make_dirs the results directory did not exist and was created at:\n{destdir}\n"
        )


def create_dir_or_ask_user_input(destdir: Path, ask_user=True):
    counter, max_attempts = 0, 10
    while not destdir.exists() and counter < max_attempts:
        answer = "y"
        if ask_user:
            answer = input(
                f"Directory to store files raman_fitting:\n{destdir}\nCan this be folder be created? (y/n)"
            )
            if "y" in answer.lower():
                destdir.mkdir(exist_ok=True, parents=True)

        if "y" not in answer.lower():
            new_path_user = input(
                "Please provide the directory to store files raman_fitting:"
            )
            try:
                new_path = Path(new_path_user).resolve()
            except Exception as e:
                print(f"Exception: {e}")
                counter += 1
            destdir = new_path

        logger.info(f"Directory created: {destdir}")
    return destdir
