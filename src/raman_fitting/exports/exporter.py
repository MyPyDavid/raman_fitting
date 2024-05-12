from dataclasses import dataclass
from typing import Dict, Any
from raman_fitting.config.path_settings import (
    RunModes,
    initialize_run_mode_paths,
    ExportPathSettings,
)
from raman_fitting.config import settings

from raman_fitting.exports.plotting_fit_results import fit_spectrum_plot
from raman_fitting.exports.plotting_raw_data import raw_data_spectra_plot


from loguru import logger

from .models import ExportResultSet


class ExporterError(Exception):
    """Error occured during the exporting functions"""


@dataclass
class ExportManager:
    run_mode: RunModes
    fit_results: Dict[str, Any] | None = None
    exports: ExportResultSet | None = None

    def __post_init__(self):
        self.paths = initialize_run_mode_paths(
            self.run_mode, user_package_home=settings.destination_dir
        )

    def export_files(self):
        # breakpoint() self.results
        exports = []
        for group_name, group_results in self.fit_results.items():
            for sample_id, sample_results in group_results.items():
                export_dir = self.paths.results_dir / group_name / sample_id
                export_paths = ExportPathSettings(results_dir=export_dir)

                export_results = ExportResultSet()
                try:
                    raw_data_spectra_plot_results = raw_data_spectra_plot(
                        sample_results["fit_results"], export_paths=export_paths
                    )
                    export_results += raw_data_spectra_plot_results
                except Exception as exc:
                    logger.error(f"Plotting error, raw_data_spectra_plot: {exc}")

                try:
                    fit_spectrum_plot_results = fit_spectrum_plot(
                        sample_results["fit_results"], export_paths=export_paths
                    )
                    export_results += fit_spectrum_plot_results
                except Exception as exc:
                    logger.error(f"plotting error fit_spectrum_plot: {exc}")
                    raise exc from exc

                exports.append(
                    {
                        "sample": sample_results["fit_results"],
                        "export_paths": export_paths,
                        "results": export_results,
                    }
                )
        return exports
