# wrapper that prevents forcing import of heavy dependencies (the C library) unless required
def compute(*args, **kwargs):
    from .eqcorr2d_engine import compute as _compute
    return _compute(*args, **kwargs)
