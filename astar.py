from heapq import heappop, heappush
from copy import deepcopy

def astar(start, h):
    frontier = []
    heappush(frontier, (0 + h(start, None), start))

    discovered = {str(start): (None, 0)}

    while frontier:
        current_f, current_node = heappop(frontier)

        print(current_node.conflicts_count(), current_f)

        current_g = discovered[str(current_node)][1]

        if current_node.is_final():
          break

        for p in current_node.get_neighbours():
            cost_g = current_g + 1
            cost_h = h(current_node, p)
            cost_f = cost_h + cost_g
            old_node = deepcopy(current_node)
            st = current_node.apply_action(action=p)
            current_node = old_node

            if str(st) not in discovered or cost_g < discovered[str(st)][1]:
                discovered[str(st)] = (current_node, cost_g)
                heappush(frontier, (cost_f, st))

    return current_node, len(discovered.keys())
