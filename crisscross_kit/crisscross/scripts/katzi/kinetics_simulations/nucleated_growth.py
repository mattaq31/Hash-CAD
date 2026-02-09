"""
Nucleated growth toy model with a reversible nucleus AND an explicit "incorporated monomers"
state variable.

Species:
  A(t): free monomer
  N(t): nucleus (contains 2 monomers each)
  P(t): polymer count (number concentration of polymers, not polymer mass)
  B(t): incorporated monomers in polymers (polymerized "mass" in monomer units)

Reactions:
1) A + A  --k_n-->  N
2) N      --k_d-->  2A                 (nucleus dissolves, regenerates monomers)
3) N + A  --k_g-->  P                  (activation / seeding a polymer)
4) P + A  --k_gp--> P                  (growth; increases polymer mass but not polymer count)

ODEs (mass action):
dA/dt = -2 k_n A^2  - k_g A N  - k_gp A P  + 2 k_d N
dN/dt =  +  k_n A^2 - k_g A N  - k_d N
dP/dt =  +  k_g A N
dB/dt =  +3 k_g A N + 1 k_gp A P

Why dB/dt has "3 k_g A N":
- When N + A -> P happens, you create a new polymer that contains:
  2 monomers from N + 1 monomer from A = 3 monomers incorporated into polymer mass.

Mass conservation check:
  A + 2N + B = constant = A0  (up to numerical error)

This script:
- integrates with RK4 (no scipy needed)
- plots:
    (i) polymerized fraction B/A0  (your "incorporated monomers" observable)
    (ii) A/A0, 2N/A0, B/A0 and mass check
    (iii) P (polymer count), optional
- parameters are easy to change in the __main__ block
"""

import numpy as np
import matplotlib.pyplot as plt


def rhs(A, N, P, B, k_n, k_d, k_g, k_gp):
    dA = -2.0 * k_n * A * A - k_g * A * N - k_gp * A * P + 2.0 * k_d * N
    dN = +1.0 * k_n * A * A - k_g * A * N - k_d * N
    dP = +1.0 * k_g * A * N
    dB = +3.0 * k_g * A * N + 1.0 * k_gp * A * P
    return dA, dN, dP, dB


def integrate_rk4(
    k_n,
    k_d,
    k_g,
    k_gp,
    A0=1.0,
    N0=0.0,
    P0=0.0,
    B0=0.0,
    t_max=200.0,
    n_steps=20000,
):
    t = np.linspace(0.0, t_max, int(n_steps))
    h = t[1] - t[0]

    A = np.empty_like(t)
    N = np.empty_like(t)
    P = np.empty_like(t)
    B = np.empty_like(t)

    A[0] = float(A0)
    N[0] = float(N0)
    P[0] = float(P0)
    B[0] = float(B0)

    for i in range(len(t) - 1):
        Ai, Ni, Pi, Bi = A[i], N[i], P[i], B[i]

        k1A, k1N, k1P, k1B = rhs(Ai, Ni, Pi, Bi, k_n, k_d, k_g, k_gp)
        k2A, k2N, k2P, k2B = rhs(
            Ai + 0.5 * h * k1A, Ni + 0.5 * h * k1N, Pi + 0.5 * h * k1P, Bi + 0.5 * h * k1B,
            k_n, k_d, k_g, k_gp
        )
        k3A, k3N, k3P, k3B = rhs(
            Ai + 0.5 * h * k2A, Ni + 0.5 * h * k2N, Pi + 0.5 * h * k2P, Bi + 0.5 * h * k2B,
            k_n, k_d, k_g, k_gp
        )
        k4A, k4N, k4P, k4B = rhs(
            Ai + h * k3A, Ni + h * k3N, Pi + h * k3P, Bi + h * k3B,
            k_n, k_d, k_g, k_gp
        )

        A[i + 1] = Ai + (h / 6.0) * (k1A + 2.0 * k2A + 2.0 * k3A + k4A)
        N[i + 1] = Ni + (h / 6.0) * (k1N + 2.0 * k2N + 2.0 * k3N + k4N)
        P[i + 1] = Pi + (h / 6.0) * (k1P + 2.0 * k2P + 2.0 * k3P + k4P)
        B[i + 1] = Bi + (h / 6.0) * (k1B + 2.0 * k2B + 2.0 * k3B + k4B)

        """
        Numerical safety:
        Small negatives can happen from finite step size. Clip to 0.
        (If this bothers you, reduce step size by increasing n_steps.)
        """
        if A[i + 1] < 0.0:
            A[i + 1] = 0.0
        if N[i + 1] < 0.0:
            N[i + 1] = 0.0
        if P[i + 1] < 0.0:
            P[i + 1] = 0.0
        if B[i + 1] < 0.0:
            B[i + 1] = 0.0

    return t, A, N, P, B


def plot_results(t, A, N, P, B, A0, title=""):
    frac_free = A / A0
    frac_nucleus = (2.0 * N) / A0
    frac_polymerized = B / A0
    mass_check = frac_free + frac_nucleus + frac_polymerized

    # ---- (1) Polymerized fraction only ----
    plt.figure(figsize=(7.6, 4.8))
    plt.plot(t, frac_polymerized)
    plt.xlabel("Time")
    plt.ylabel("Polymerized fraction (B/A₀)")
    plt.ylim(-0.02, 1.02)
    plt.title(title if title else "Polymerized monomers")
    plt.tight_layout()

    # ---- (2) Mass partition plot (KEEP) ----
    plt.figure(figsize=(7.6, 4.8))
    plt.plot(t, frac_free, label="A/A₀ (free)")
    plt.plot(t, frac_nucleus, label="2N/A₀ (in nuclei)")
    plt.plot(t, frac_polymerized, label="B/A₀ (polymerized)")
    plt.plot(t, mass_check, "--", label="mass check")
    plt.xlabel("Time")
    plt.ylabel("Fraction of initial monomers")
    plt.ylim(-0.02, 1.05)
    plt.title("Mass partition")
    plt.legend()
    plt.tight_layout()

    # ---- (3) NEW: total incorporated mass (nucleus + polymer) ----
    incorporated = frac_nucleus + frac_polymerized

    plt.figure(figsize=(7.6, 4.8))
    plt.plot(t, incorporated)
    plt.xlabel("Time")
    plt.ylabel("Incorporated monomer fraction")
    plt.ylim(-0.02, 1.02)
    plt.title("Monomers incorporated in nuclei OR polymers")
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    """
    Change parameters here.
    Tip: S-curves appear when there is a bottleneck (e.g., very small k_n, or large k_d relative to k_g*A0).
    """

    # ---- Parameters to edit ----
    params = {
        "k_n": 0.5,     # nucleation A+A -> N
        "k_d": 4,      # nucleus death N -> 2A
        "k_g": 0.05,      # activation N + A -> P
        "k_gp": 0.05,     # growth P + A -> P (mass increases via B)
        "A0": 1.0,       # initial monomer
        "N0": 0.0,
        "P0": 0.0,
        "B0": 0.0,
        "t_max": 10.0,
        "n_steps": 50000,
    }

    t, A, N, P, B = integrate_rk4(
        k_n=params["k_n"],
        k_d=params["k_d"],
        k_g=params["k_g"],
        k_gp=params["k_gp"],
        A0=params["A0"],
        N0=params["N0"],
        P0=params["P0"],
        B0=params["B0"],
        t_max=params["t_max"],
        n_steps=params["n_steps"],
    )

    title = (
        f"Polymerized fraction B/A0  "
        f"(k_n={params['k_n']}, k_d={params['k_d']}, k_g={params['k_g']}, k_gp={params['k_gp']}, A0={params['A0']})"
    )
    plot_results(t, A, N, P, B, A0=params["A0"], title=title)
