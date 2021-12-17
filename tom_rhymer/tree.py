from dataclasses import dataclass
from copy import deepcopy


@dataclass
class IterStats:
    n_matches_todo: int
    n_skips_allowed: int

    def __post_init__(self):
        pass

    def clone(self):
        return deepcopy(self)


class Node:
    def __init__(self):
        self._children = dict()
        self._values = []

    def add(self, tag):
        return self._children.setdefault(tag, Node())

    def set_value(self, value):
        self._values.append(value)

    def iterate_on_nodes(self, path, iter_stats: IterStats):
        iter_stats = iter_stats.clone()

        if iter_stats.n_matches_todo <= 0:
            yield from self._values
            for child in self._children.values():
                yield from child.iterate_on_nodes(path[1:], iter_stats)

        if not path:
            return

        # Iterate on all but matched node:
        if iter_stats.n_skips_allowed > 0:
            for tag, node in self._children.items():
                if tag != path[0]:
                    iter_stats.n_skips_allowed -= 1
                    yield from node.iterate_on_nodes(path[1:], iter_stats)

        # Iterate on valid matches:
        node = self._children.get(path[0])
        if node:
            iter_stats.n_matches_todo -= 1
            yield from node.iterate_on_nodes(path[1:], iter_stats)


class Tree:
    def __init__(self):
        self._roots = dict()

    def add(self, path, value):
        root_tag = path[0]
        node = self._roots.setdefault(root_tag, Node())
        for tag in path[1:]:
            node = node.add(tag)
        node.set_value(value)

    def iterate_on_nodes(
            self,
            path,
            min_n_matches,
            max_n_skips,
    ):
        min_n_matches = min(len(path), min_n_matches)
        root_tag = path[0]
        node = self._roots.get(root_tag)
        if not node:
            return
        iter_stats = IterStats(
            n_matches_todo=min_n_matches - 1,
            n_skips_allowed=max_n_skips,
        )
        yield from node.iterate_on_nodes(path[1:], iter_stats)
