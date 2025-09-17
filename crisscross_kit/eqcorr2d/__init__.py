def compute(*args, **kwargs):
    from .eqcorr2d_engine import compute as _compute
    return _compute(*args, **kwargs)
