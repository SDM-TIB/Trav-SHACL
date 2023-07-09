# -*- coding: utf-8 -*-
__author__ = 'Philipp D. Rohde'

from enum import Enum


class GraphTraversal(Enum):
    """This enum is used to specify the algorithm used for graph traversal."""
    BFS = 'Breadth-first search'
    DFS = 'Depth-first search'

    def traverse_graph(self, dependencies, reversed_dependencies, starting_point, one_component=False):
        nodes = list(dependencies.keys())
        visited = []
        if self == GraphTraversal.DFS:
            while len(nodes) > 0:
                self._dfs(visited, dependencies, reversed_dependencies, starting_point)
                if one_component:  # only one connected component allowed, so drop the other nodes
                    nodes = []
                else:
                    [nodes.remove(v) for v in visited if v in nodes]
                    starting_point = nodes[0] if len(nodes) > 0 else None
        elif self == GraphTraversal.BFS:
            while len(nodes) > 0:
                self._bfs(visited, dependencies, reversed_dependencies, starting_point)
                if one_component:  # only one connected component allowed, so drop the other nodes
                    nodes = []
                else:
                    [nodes.remove(v) for v in visited if v in nodes]
                    starting_point = nodes[0] if len(nodes) > 0 else None
        return visited

    def _dfs(self, visited, dependencies, reversed_dependencies, node):
        """Implementation of depth-first search with the ability to go back
        if the algorithm is in a sink but there are still unvisited nodes."""
        # TODO: rearrange the graph (do not prioritize dependencies, i.e., use edges = dep + rev_dep)?
        if node not in visited:
            visited.append(node)
            for neighbour in dependencies[node]:
                self._dfs(visited, dependencies, reversed_dependencies, neighbour)
            if sorted(visited) != sorted(dependencies.keys()):
                for neighbour in reversed_dependencies[node]:
                    self._dfs(visited, dependencies, reversed_dependencies, neighbour)
        elif node in visited and sorted(visited) != sorted(dependencies.keys()):
            for neighbour in dependencies[node]:
                if neighbour not in visited:
                    self._dfs(visited, dependencies, reversed_dependencies, neighbour)
            for neighbour in reversed_dependencies[node]:
                if neighbour not in visited:
                    self._dfs(visited, dependencies, reversed_dependencies, neighbour)

    def _bfs(self, visited, dependencies, reversed_dependencies, node):
        """Implementation of breadth-first search.
        Rearranges the graph, i.e., dependencies are not prioritized."""
        edges = self._edges(dependencies, reversed_dependencies)
        queue = [node]
        visited.append(node)
        while queue:
            node = queue.pop(0)
            for neighbour in edges[node]:
                if neighbour not in visited:
                    visited.append(neighbour)
                    queue.append(neighbour)

    @staticmethod
    def _edges(dependencies, reversed_dependencies):
        edges = {}
        for k in dependencies.keys():
            edges[k] = []
            edges[k].extend(dependencies[k])
            edges[k].extend(reversed_dependencies[k])
        return edges
