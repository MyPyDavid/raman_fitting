from typing import Dict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.axes import Axes

from matplotlib.text import Text
from matplotlib.ticker import AutoMinorLocator

from raman_fitting.imports.samples.models import SampleMetaData
from raman_fitting.models.fit_models import SpectrumFitModel


from raman_fitting.config.path_settings import ExportPathSettings
from raman_fitting.models.splitter import RegionNames
from raman_fitting.delegating.models import AggregatedSampleSpectrumFitResult

from loguru import logger


matplotlib.rcParams.update({"font.size": 14})
FIT_REPORT_MIN_CORREL = 0.7
DEFAULT_SECOND_ORDER_MODEL = "2nd_4peaks"


def fit_spectrum_plot(
    aggregated_spectra: Dict[RegionNames, AggregatedSampleSpectrumFitResult],
    export_paths: ExportPathSettings | None = None,
    plot_annotation=True,
    plot_residuals=True,
):  # pragma: no cover
    for region_name, region_aggregated_spectrum in aggregated_spectra.items():
        sources = region_aggregated_spectrum.aggregated_spectrum.sources
        sample = sources[0].file_info.sample

        second_model = None
        if (
            region_name == RegionNames.first_order
            and RegionNames.second_order in aggregated_spectra
        ):
            second_order = aggregated_spectra[RegionNames.second_order]
            second_model = second_order.fit_model_results.get(
                DEFAULT_SECOND_ORDER_MODEL
            )
        for (
            model_name,
            current_model,
        ) in region_aggregated_spectrum.fit_model_results.items():
            logger.warning(
                f"Starting to plot for {sample.id}, {region_name} {model_name}."
            )

            prepare_combined_spectrum_fit_result_plot(
                current_model,
                second_model,
                sample,
                export_paths,
                plot_annotation=plot_annotation,
                plot_residuals=plot_residuals,
            )


def prepare_combined_spectrum_fit_result_plot(
    first_model: SpectrumFitModel,
    second_model: SpectrumFitModel,
    sample: SampleMetaData,
    export_paths: ExportPathSettings,
    plot_annotation=True,
    plot_residuals=True,
):
    first_model_name = first_model.model.name

    plt.figure(figsize=(28, 24))
    gs = gridspec.GridSpec(4, 1, height_ratios=[4, 1, 4, 1])
    ax = plt.subplot(gs[0])
    ax_res = plt.subplot(gs[1])
    ax.set_title(f"{sample.id}, {first_model_name}")

    fit_plot_first(ax, ax_res, first_model, plot_residuals=plot_residuals)
    _bbox_artists = None
    if plot_annotation:
        annotate_report_first = prepare_annotate_fit_report_first(
            ax, first_model.fit_result
        )
        _bbox_artists = (annotate_report_first,)

    if second_model is not None:
        ax2nd = plt.subplot(gs[2])
        ax2nd_res = plt.subplot(gs[3])
        fit_plot_second(ax2nd, ax2nd_res, second_model, plot_residuals=plot_residuals)
        if plot_annotation:
            annotate_report_second = prepare_annotate_fit_report_second(
                ax2nd, second_model.fit_result
            )
            if annotate_report_second is not None:
                _bbox_artists = (annotate_report_first, annotate_report_second)

    # set axes labels and legend
    set_axes_labels_and_legend(ax)

    plot_special_si_components(ax, first_model)
    if export_paths is not None:
        savepath = export_paths.plots.joinpath(f"Model_{first_model_name}").with_suffix(
            ".png"
        )
        plt.savefig(
            savepath,
            dpi=100,
            bbox_extra_artists=_bbox_artists,
            bbox_inches="tight",
        )
        logger.debug(f"Plot saved to {savepath}")
    plt.close()


def fit_plot_first(
    ax, ax_res, first_model: SpectrumFitModel, plot_residuals: bool = True
) -> matplotlib.text.Text | None:
    first_result = first_model.fit_result
    first_components = first_model.fit_result.components
    first_eval_comps = first_model.fit_result.eval_components()
    first_model_name = first_model.model.name

    ax.grid(True, "both")
    ax_res.grid(True, "both")
    ax.get_yaxis().set_tick_params(direction="in")
    ax.get_xaxis().set_tick_params(direction="in")

    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.tick_params(which="both", direction="in")
    ax.set_facecolor("oldlace")
    ax_res.set_facecolor("oldlace")
    ax.plot(
        first_model.spectrum.ramanshift,
        first_result.best_fit,
        label=first_model_name,
        lw=3,
        c="r",
    )
    ax.plot(
        first_model.spectrum.ramanshift,
        first_result.data,
        label="Data",
        lw=3,
        c="grey",
        alpha=0.8,
    )

    if plot_residuals:
        ax_res.plot(
            first_model.spectrum.ramanshift,
            first_result.residual,
            label="Residual",
            lw=3,
            c="k",
            alpha=0.8,
        )

    for _component in first_components:  # automatic color cycle 'cyan' ...
        peak_name = _component.prefix.rstrip("_")
        ax.plot(
            first_model.spectrum.ramanshift,
            first_eval_comps[_component.prefix],
            ls="--",
            lw=4,
            label=peak_name,
        )
        center_col = _component.prefix + "center"
        ax.annotate(
            f"{peak_name}:\n {first_result.best_values[center_col]:.0f}",
            xy=(
                first_result.best_values[center_col] * 0.97,
                0.7 * first_result.params[_component.prefix + "height"].value,
            ),
            xycoords="data",
        )


def fit_plot_second(
    ax2nd, ax2nd_res, second_model: SpectrumFitModel, plot_residuals: bool = True
) -> None:
    if second_model:
        second_result = second_model.fit_result
        second_components = second_model.fit_result.components
        second_eval_comps = second_model.fit_result.eval_components()
        second_model_name = second_model.model.name
    else:
        second_components = []
        second_result = None
        second_model_name = None
        second_eval_comps = None
    if second_model:
        ax2nd.grid(True)
        ax2nd_res.grid(True)
        ax2nd.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax2nd.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax2nd.tick_params(which="both", direction="in")
        ax2nd.set_facecolor("oldlace")
        ax2nd_res.set_facecolor("oldlace")
    if second_result is not None:
        ax2nd.plot(
            second_model.spectrum.ramanshift,
            second_result.best_fit,
            label=second_model_name,
            lw=3,
            c="r",
        )
        ax2nd.plot(
            second_model.spectrum.ramanshift,
            second_result.data,
            label="Data",
            lw=3,
            c="grey",
            alpha=0.5,
        )
        if plot_residuals:
            ax2nd_res.plot(
                second_model.spectrum.ramanshift,
                second_result.residual,
                label="Residual",
                lw=3,
                c="k",
                alpha=0.8,
            )

    for _component in second_components:  # automatic color cycle 'cyan' ...
        if second_eval_comps is None:
            continue

        peak_name = _component.prefix.rstrip("_")
        ax2nd.plot(
            second_model.spectrum.ramanshift,
            second_eval_comps[_component.prefix],
            ls="--",
            lw=4,
            label=peak_name,
        )
        center_col = _component.prefix + "center"
        ax2nd.annotate(
            f"{peak_name}\n {second_result.best_values[center_col]:.0f}",
            xy=(
                second_result.best_values[center_col] * 0.97,
                0.8 * second_result.params[_component.prefix + "height"].value,
            ),
            xycoords="data",
        )
        ax2nd.set_ylim(-0.02, second_result.data.max() * 1.5)

    set_axes_labels_and_legend(ax2nd)


def prepare_annotate_fit_report_second(ax2nd, second_result) -> Text:
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    annotate_report_second = ax2nd.text(
        1.01,
        0.7,
        second_result.fit_report(min_correl=FIT_REPORT_MIN_CORREL),
        transform=ax2nd.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=props,
    )

    return annotate_report_second


def prepare_annotate_fit_report_first(ax, first_result):
    fit_report = first_result.fit_report(min_correl=FIT_REPORT_MIN_CORREL)
    if len(fit_report) > -1:
        fit_report = fit_report.replace("prefix='D3_'", "prefix='D3_' \n")
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)

    annotate_report_first = ax.text(
        1.01,
        1,
        fit_report,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=props,
    )
    return annotate_report_first


def plot_special_si_components(ax, first_model):
    first_result = first_model.fit_result
    si_components = filter(lambda x: x.prefix.startswith("Si"), first_result.components)
    first_eval_comps = first_model.fit_result.eval_components()
    for si_comp in si_components:
        si_result = si_comp
        ax.plot(
            first_model.spectrum.ramanshift,
            first_eval_comps[si_comp.prefix],
            "b--",
            lw=4,
            label="Si_substrate",
        )
        if si_result.params[si_comp.prefix + "fwhm"] > 1:
            ax.annotate(
                "Si_substrate:\n %.0f" % si_result.params["Si1_center"].value,
                xy=(
                    si_result.params["Si1_center"].value * 0.97,
                    0.8 * si_result.params["Si1_height"].value,
                ),
                xycoords="data",
            )


def set_axes_labels_and_legend(ax: Axes):
    # set axes labels and legend
    ax.legend(loc=1)
    ax.set_xlabel("Raman shift (cm$^{-1}$)")
    ax.set_ylabel("normalized I / a.u.")
