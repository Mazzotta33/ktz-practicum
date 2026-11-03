"""Independent min-cost-flow oracle for solver regression tests (stdlib only)."""
from collections import deque


def solve(supply, demand, costs):
    m, n = len(supply), len(demand)
    source, sink = m + n, m + n + 1
    graph = [[] for _ in range(sink + 1)]

    def edge(u, v, capacity, cost):
        forward = [v, capacity, cost, len(graph[v])]
        backward = [u, 0, -cost, len(graph[u])]
        graph[u].append(forward)
        graph[v].append(backward)

    for i, amount in enumerate(supply):
        edge(source, i, amount, 0)
    for j, amount in enumerate(demand):
        edge(m + j, sink, amount, 0)
    total = sum(supply)
    for i in range(m):
        for j in range(n):
            edge(i, m + j, total, costs[i][j])
    flow = objective = 0
    while flow < total:
        distance = [float('inf')] * len(graph)
        distance[source] = 0
        queue, queued, previous = deque([source]), {source}, {}
        while queue:
            u = queue.popleft()
            queued.remove(u)
            for index, (v, capacity, cost, _) in enumerate(graph[u]):
                if capacity > 0 and distance[v] > distance[u] + cost:
                    distance[v] = distance[u] + cost
                    previous[v] = (u, index)
                    if v not in queued:
                        queue.append(v)
                        queued.add(v)
        if sink not in previous:
            raise ValueError('No feasible flow')
        amount, v = total - flow, sink
        while v != source:
            u, index = previous[v]
            amount = min(amount, graph[u][index][1])
            v = u
        v = sink
        while v != source:
            u, index = previous[v]
            e = graph[u][index]
            e[1] -= amount
            graph[v][e[3]][1] += amount
            v = u
        flow += amount
        objective += amount * distance[sink]
    return {'objective': objective}
