from typing import Sequence, Tuple, Dict

from raman_fitting.models.deconvolution.spectrum_regions import (
    get_default_regions_from_toml_files,
    SpectrumRegionLimits,
    RegionNames,
)

import matplotlib.pyplot as plt
from lmfit import Model as LMFitModel

from loguru import logger


CMAP_OPTIONS_DEFAULT = ("Dark2", "tab20")
DEFAULT_COLOR = (0.4, 0.4, 0.4, 1.0)
COLOR_BLACK = (0, 0, 0, 1)  # black as fallback default color
PLOT_AXES_WIDTH = 3

RAW_MEAN_SPEC_FMT = dict(c="k", alpha=0.7, lw=3)
RAW_SOURCES_SPEC_FMT = dict(alpha=0.4, lw=2)


def get_plot_region_axes(
    nrows: int | None = None, regions: Dict[str, SpectrumRegionLimits] | None = None
) -> Dict[RegionNames, Tuple[int, int]]:
    if regions is None:
        regions = get_default_regions_from_toml_files()
    horizontal_axis = 0
    nrows = PLOT_AXES_WIDTH if nrows is None else nrows
    regions_axes = {}
    for n, region in enumerate(regions.values()):
        if "normalization" in region.name:
            continue
        _i = n + 1
        vertical_axis = _i if _i <= nrows else _i % nrows
        regions_axes[region.name] = (vertical_axis, horizontal_axis)
        if not _i % nrows:
            horizontal_axis += 1

    return regions_axes


def get_cmap_list(
    length: int,
    cmap_options: Tuple = CMAP_OPTIONS_DEFAULT,
    default_color: Tuple = DEFAULT_COLOR,
) -> Tuple | None:
    lst = list(range(length))
    if not lst:
        return None

    # set fallback color from class
    if isinstance(default_color, tuple) and default_color is not None:
        if len(default_color) == 4:
            cmap = [default_color for _ in lst]
            return cmap
    elif default_color is None:
        cmap = [DEFAULT_COLOR for _ in lst]
    else:
        raise ValueError(f"default color is not tuple but {type(default_color)}")

    # set cmap colors from cmap options
    if cmap_options:
        try:
            pltcmaps = [plt.get_cmap(cmap) for cmap in cmap_options]
            # Take shortest colormap but not
            cmap = min(
                [i for i in pltcmaps if len(lst) <= len(i.colors)],
                key=lambda x: len(x.colors),
                default=cmap,
            )
            # if succesfull
            if "ListedColormap" in str(type(cmap)):
                cmap = cmap.colors

        except Exception as exc:
            logger.warning(f"get_cmap_list error setting cmap colors:{exc}")

    return cmap


def assign_colors_to_peaks(selected_models: Sequence[LMFitModel]) -> dict:
    cmap_get = get_cmap_list(len(selected_models))
    annotated_models = {}
    for n, peak in enumerate(selected_models):
        color = ", ".join([str(i) for i in cmap_get[n]])
        lenpars = len(peak.param_names)
        res = {"index": n, "color": color, "lenpars": lenpars, "peak": peak}
        annotated_models[peak.prefix] = res
    return annotated_models


def __repr__(self):
    _repr = "Validated Peak model collection"
    if self.selected_models:
        _selmods = f", {len(self.selected_models)} models from: " + "\n\t- "
        _repr += _selmods
        _joinmods = "\n\t- ".join(
            [f"{i.peak_group}: {i.model_inst} \t" for i in self.selected_models]
        )
        _repr += _joinmods
    else:
        _repr += ", empty selected models"
    return _repr
