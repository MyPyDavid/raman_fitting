from lmfit import Parameter


def join_prefix_suffix(prefix: str, suffix: str) -> str:
    prefix_ = prefix.rstrip("_")
    suffix_ = suffix.lstrip("_")
    if suffix_ in prefix:
        return prefix_
    return f"{prefix_}_{suffix_}"


def prepare_text_from_param(param: Parameter) -> str:
    text = ""
    if not param:
        return text
    _ptext = ""
    _val = param.value
    _min = param.min
    if _min != _val:
        _ptext += f"{_min} < "
    _ptext += f"{_val}"
    _max = param.max
    if _max != _val:
        _ptext += f" > {_max}"
    text += f", center : {_ptext}"
    return text
