"""Check GMIN behavior and compare exact vertex covers against exhaustive solutions."""

from itertools import combinations_with_replacement
import random
import unittest
from unittest.mock import patch

from orthoseq_generator.vertex_cover_algorithms import (
    cleanup_vertex_cover,
    exact_vertex_cover,
    find_uncovered_edges,
    greedy_vertex_cover_gmin,
)


class TestGreedyVertexCoverGmin(unittest.TestCase):
    """Exercise small graphs including self-edges and isolated vertices."""

    def test_all_four_vertex_graphs(self):
        """Every result must cover all edges and require no further cleanup."""
        V = [10, 20, 30, 40]
        possible_edges = list(combinations_with_replacement(V, 2))
        for mask in range(1 << len(possible_edges)):
            E = [edge for i, edge in enumerate(possible_edges) if mask & (1 << i)]
            for tiebreak in [None, "rule"]:
                with self.subTest(mask=mask, tiebreak=tiebreak):
                    random.seed(mask)
                    vertex_cover = greedy_vertex_cover_gmin(V, E, tiebreak=tiebreak)
                    self.assertTrue(vertex_cover.issubset(set(V)))
                    self.assertFalse(find_uncovered_edges(E, vertex_cover))
                    self.assertEqual(cleanup_vertex_cover(E, vertex_cover.copy()), vertex_cover)

    def test_rule_tiebreak_candidates(self):
        """The rule must exclude tied candidates with more minimum-degree neighbors."""
        V = list(range(7))
        E = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 6), (6, 3)]
        for tiebreak, expected in [(None, [0, 1, 4, 5, 6]), ("rule", [0, 1, 4, 6])]:
            with patch("orthoseq_generator.vertex_cover_algorithms.random.choice") as choice:
                choice.side_effect = lambda vertices: vertices[0]
                greedy_vertex_cover_gmin(V, E, tiebreak=tiebreak)
                self.assertEqual(choice.call_args_list[0].args[0], expected)

    def test_empty_graph_and_iterables(self):
        """Isolates survive and iterable inputs with duplicate edges remain supported."""
        self.assertEqual(greedy_vertex_cover_gmin([], []), set())
        self.assertEqual(greedy_vertex_cover_gmin(["isolated"], []), set())
        V = ["isolated", "loop", "neighbor"]
        E = [("loop", "loop"), ("loop", "neighbor"), ("neighbor", "loop")]
        self.assertEqual(greedy_vertex_cover_gmin(iter(V), iter(E)), {"loop"})
        self.assertEqual(V, ["isolated", "loop", "neighbor"])
        self.assertEqual(len(E), 3)


class TestExactVertexCover(unittest.TestCase):
    """Verify optimality independently by enumerating all candidate covers on small graphs."""

    def test_all_four_vertex_graphs(self):
        """Match brute force for every four-vertex graph, including self-edges."""
        V = [10, 20, 30, 40]
        possible_edges = list(combinations_with_replacement(V, 2))
        for mask in range(1 << len(possible_edges)):
            E = [edge for i, edge in enumerate(possible_edges) if mask & (1 << i)]
            covers = [{v for i, v in enumerate(V) if subset & (1 << i)} for subset in range(1 << len(V))]
            minimum_size = min(len(cover) for cover in covers if not find_uncovered_edges(E, cover))
            with self.subTest(mask=mask):
                vertex_cover, optimal = exact_vertex_cover(V, E, time_limit=None)
                self.assertTrue(optimal)
                self.assertFalse(find_uncovered_edges(E, vertex_cover))
                self.assertEqual(len(vertex_cover), minimum_size)

    def test_timeout(self):
        """A stopped search must return a feasible cover without claiming optimality."""
        E = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
        vertex_cover, optimal = exact_vertex_cover(range(5), E, time_limit=0)
        self.assertFalse(optimal)
        self.assertFalse(find_uncovered_edges(E, vertex_cover))

    def test_empty_graph(self):
        """An empty input has an empty optimal cover."""
        self.assertEqual(exact_vertex_cover([], []), (set(), True))


if __name__ == "__main__":
    unittest.main()
