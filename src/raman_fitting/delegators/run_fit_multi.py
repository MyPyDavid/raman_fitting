from typing import Dict, List

from loguru import logger
from mpire import WorkerPool

from raman_fitting.models.fit_models import SpectrumFitModel


def run_fit_multi(**kwargs) -> SpectrumFitModel:
    #  include optional https://lmfit.github.io/lmfit-py/model.html#saving-and-loading-modelresults
    spectrum = kwargs.pop("spectrum")
    model = kwargs.pop("model")
    lmfit_model = model["lmfit_model"]
    region = kwargs.pop("region")
    import time

    lmfit_kwargs = {}
    if "method" not in kwargs:
        lmfit_kwargs["method"] = "leastsq"

    init_params = lmfit_model.make_params()
    start_time = time.time()
    x, y = spectrum["ramanshift"], spectrum["intensity"]
    out = lmfit_model.fit(y, init_params, x=x, **lmfit_kwargs)  # 'leastsq'
    end_time = time.time()
    elapsed_seconds = abs(start_time - end_time)
    elapsed_time = elapsed_seconds
    logger.debug(
        f"Fit with model {model['name']} on {region} success: {out.success} in {elapsed_time:.2f}s."
    )
    return out


def run_fit_multiprocessing(
    spec_fits: List[SpectrumFitModel],
) -> Dict[str, SpectrumFitModel]:
    spec_fits_dumps = [i.model_dump() for i in spec_fits]

    with WorkerPool(n_jobs=4, use_dill=True) as pool:
        results = pool.map(
            run_fit_multi, spec_fits_dumps, progress_bar=True, progress_bar_style="rich"
        )
    #  patch spec_fits, setattr fit_result
    fit_model_results = {}
    for result in results:
        _spec_fit_search = [
            i for i in spec_fits if i.model.lmfit_model.name == result.model.name
        ]
        if len(_spec_fit_search) != 1:
            continue
        _spec_fit = _spec_fit_search[0]
        _spec_fit.fit_result = result
        fit_model_results[_spec_fit.model.name] = _spec_fit
    return fit_model_results
