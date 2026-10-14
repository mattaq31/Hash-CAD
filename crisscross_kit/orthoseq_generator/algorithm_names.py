"""Build consistent algorithm labels and recognize historical names without rewriting saved data."""

import re

LEGACY_ALGORITHM_NAMES = {
    "vertex_cover": "vertex_cover_GMAX_rule_offline",
    "vertex_cover_GMIN": "vertex_cover_GMIN_rule_offline",
    "hybrid_offline": "hybrid_GMAX_rule_offline",
    "hybrid_search": "hybrid_GMAX_rule",
    "naive": "naive_rand_offline",
    "naive_ordered": "naive_rank_offline",
    "naive_search": "naive_rand",
}


def build_algorithm_name(workflow, heuristics="Gmax", tiebreak="rule", *, offline=False, ordering="random", bare=False):
    """Name a search by workflow, heuristic and tie mode, with offline execution last."""
    if workflow == "naive":
        if ordering not in ("random", "weaker_first"):
            raise ValueError("ordering must be 'random' or 'weaker_first'.")
        name = "naive_rank" if ordering == "weaker_first" else "naive_rand"
    elif workflow in ("vertex_cover", "hybrid"):
        if heuristics not in ("Gmax", "Gmin"):
            raise ValueError("heuristics must be 'Gmax' or 'Gmin'.")
        if tiebreak not in ("rule", "rank", None):
            raise ValueError("tiebreak must be 'rule', 'rank', or None.")
        ties = "rand" if tiebreak is None else tiebreak
        name = f"{workflow}_{heuristics.upper()}_{ties}"
    else:
        raise ValueError("workflow must be 'vertex_cover', 'hybrid', or 'naive'.")
    if bare:
        if workflow != "vertex_cover":
            raise ValueError("bare applies only to vertex-cover runs without iterative refinement.")
        name += "_bare"
    return name + "_offline" if offline else name


def normalize_algorithm_name(name):
    """Recognize old labels in configs and reports while leaving unrelated names untouched."""
    if name in LEGACY_ALGORITHM_NAMES:
        return LEGACY_ALGORITHM_NAMES[name]
    comparison = re.fullmatch(r"(gmin|gmax)_(random|rule|rank)(_iterative)?", name or "")
    if comparison:
        heuristic, ties, iterative = comparison.groups()
        return build_algorithm_name(
            "vertex_cover", "Gmin" if heuristic == "gmin" else "Gmax",
            None if ties == "random" else ties, offline=True, bare=iterative is None,
        )
    return name


def algorithm_workflow(name):
    """Extract the search family for plots that intentionally compare whole workflows."""
    name = normalize_algorithm_name(name)
    if name is not None:
        for workflow in ("vertex_cover", "hybrid", "naive"):
            if name.startswith(workflow + "_"):
                return workflow
    return name
