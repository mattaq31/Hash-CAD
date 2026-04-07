import math


def analytic_independent_set_estimator(n: int, pc: float) -> int:
    """
    Analytic estimator for the intersection m* defined by:

        0 = ln(C(n, m)) + (m*(m-1)/2) * ln(1 - pc)

    Interpretation:
    - ln(C(n,m)) is the combinatorial "entropy" term.
    - (m*(m-1)/2)*ln(1-pc) is a quadratic penalty term (since ln(1-pc) < 0),
      so the sum eventually becomes negative as m grows.

    The simplest scaling estimate balances the leading behaviors for m << n:
        ln(C(n,m)) ~ m * ln(n)
        (m*(m-1)/2)*ln(1-pc) ~ -(m^2/2) * (-ln(1-pc))

    Solving m* ln(n) ~ (m*^2/2) * (-ln(1-pc)) gives:
        m* ~ 2 ln(n) / (-ln(1-pc))

    Returns:
    - An integer seed value (rounded, and clamped to at least 1).
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if not (0.0 < pc < 1.0):
        raise ValueError("pc must be in (0,1)")

    denom = -math.log(1.0 - pc)  # positive
    m_pred = 2.0 * math.log(n) / denom

    # Return a usable integer seed.
    m_int = int(round(m_pred))
    if m_int < 1:
        m_int = 1
    return m_int


def _log_binom_safe(n: int, m: int) -> float:
    """
    Numerically stable exact identity (no factorials, no gamma):

        ln(C(n,m)) = sum_{i=0}^{m-1} ln((n - i) / (m - i))

    Notes:
    - Uses symmetry C(n,m) = C(n,n-m) internally for efficiency only.
    - Safe for extremely large n (e.g. n = 4^20) provided m is moderate.
    - This computes ln(C(n,m)) from scratch each call (simple and robust).
    """
    if m < 0 or m > n:
        return float("nan")

    m = min(m, n - m)  # exact symmetry
    if m == 0:
        return 0.0

    s = 0.0
    for i in range(m):
        s += math.log((n - i) / (m - i))
    return s


def numeric_independet_set_estimator(n: int, pc: float) -> int:
    """
    Numeric estimator for the intersection m* defined by:

        0 = ln(C(n, m)) - ln(C(m, r(m))) + (m*(m-1)/2) * ln(1 - pc)

    where:
        r(m) = floor(m^2 / n)

    Returns the largest integer m >= 1 such that:
        f(m) := ln(C(n,m)) - ln(C(m,r(m))) + (m*(m-1)/2)*ln(1-pc) > 0

    Strategy:
    1) Use the analytic estimator as a seed m0.
    2) Evaluate f(m0).
       - If f(m0) <= 0, we are already past the crossing, so we walk downward.
       - If f(m0) > 0, we are before the crossing, so we walk upward.
    3) Convert the first sign-crossing to the largest feasible m (crossing - 1).

    Why this is efficient:
    - In the regimes you care about, the crossing typically occurs at
      m* = O(ln n / (-ln(1-pc))) which is usually a few 10s to 1000s,
      even if n is enormous.
    - We recompute ln(C(n,m)) from scratch each step (robust, easy to reason about).

    Important:
    - Search is performed on the full domain m in [1, n] so no crossing is
      missed due to a symmetry shortcut.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if not (0.0 < pc < 1.0):
        raise ValueError("pc must be in (0,1)")

    ln1mp = math.log(1.0 - pc)  # negative
    m_max = n

    if m_max < 1:
        return 1

    # Seed from analytic estimate, clamped into the valid search region.
    m = analytic_independent_set_estimator(n, pc)
    if m > m_max:
        m = m_max

    def f(m_: int) -> float:
        # f(m) = lnC(n,m) - lnC(m,r(m)) + (m(m-1)/2)*ln(1-pc)
        r_ = (m_ * m_) // n
        return (
            _log_binom_safe(n, m_)
            - _log_binom_safe(m_, r_)
            + 0.5 * m_ * (m_ - 1) * ln1mp
        )

    val = f(m)

    # If already <= 0, walk downward to find the boundary where f turns positive.
    if val <= 0.0:
        while m > 1:
            if f(m - 1) > 0.0:
                return m - 1
            m -= 1
        return 1 if f(1) > 0.0 else 0

    # Otherwise, walk upward until we cross to non-positive.
    while m < m_max:
        m += 1
        if f(m) <= 0.0:
            return m - 1

    # If no crossing occurs in [1, n], all tested sizes are feasible.
    return m_max
