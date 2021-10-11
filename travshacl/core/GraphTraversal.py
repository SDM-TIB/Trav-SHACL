# -*- coding: utf-8 -*-
__author__ = "Philipp D. Rohde"

from enum import Enum


class GraphTraversal(Enum):
    """This enum is used to specify the algorithm used for graph traversal."""
    BFS = "Breadth-first search"
    DFS = "Depth-first search"

    def traverse_graph(self, dependencies, reversed_dependencies, starting_point):
        visited = []
        if self == GraphTraversal.DFS:
            self.__dfs(visited, dependencies, reversed_dependencies, starting_point)
        elif self == GraphTraversal.BFS:
            self.__bfs(visited, dependencies, reversed_dependencies, starting_point)
        return visited

    def __dfs(self, visited, dependencies, reversed_dependencies, node):
        """Implementation of depth-first search with the ability to go back
        if the algorithm is in a sink but there are still unvisited nodes."""
        # TODO: rearrange the graph (do not prioritize dependencies, i.e., use edges = dep + rev_dep)?
        if node not in visited:
            visited.append(node)
            for neighbour in dependencies[node]:
                self.__dfs(visited, dependencies, reversed_dependencies, neighbour)
            if sorted(visited) != sorted(dependencies.keys()):
                for neighbour in reversed_dependencies[node]:
                    self.__dfs(visited, dependencies, reversed_dependencies, neighbour)
        elif node in visited and sorted(visited) != sorted(dependencies.keys()):
            for neighbour in dependencies[node]:
                if neighbour not in visited:
                    self.__dfs(visited, dependencies, reversed_dependencies, neighbour)
            for neighbour in reversed_dependencies[node]:
                if neighbour not in visited:
                    self.__dfs(visited, dependencies, reversed_dependencies, neighbour)

    def __bfs(self, visited, dependencies, reversed_dependencies, node):
        """Implementation of breadth-first search.
        Rearranges the graph, i.e., dependencies are not prioritized."""
        edges = self.__edges(dependencies, reversed_dependencies)
        queue = [node]
        visited.append(node)
        while queue:
            node = queue.pop(0)
            for neighbour in edges[node]:
                if neighbour not in visited:
                    visited.append(neighbour)
                    queue.append(neighbour)

    @staticmethod
    def __edges(dependencies, reversed_dependencies):
        edges = {}
        for k in dependencies.keys():
            edges[k] = []
            edges[k].extend(dependencies[k])
            edges[k].extend(reversed_dependencies[k])
        return edges
