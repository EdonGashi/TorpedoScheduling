'''Solution modeling.'''
from instance import Instance
from evaluator import create_solution_timeline

def optimize(solution, matrix):
    pass


def find_initial_solution(instance: Instance):
    '''Finds an initial solution using forward-checking.
    The initial solution guarantees that no deadline is missed,
    but does not ensure that buffer and transit constraints are
    satisfied.
    '''
    matrix = instance.create_adjacency_matrix()
    num_bf = len(instance.bf_schedules)
    num_converters = len(instance.converter_schedules)
    sorted_converters = sorted(instance.converter_schedules,
                               key=lambda x: matrix[x.converter_id].domain_size)

    # We are using an explicit preallocated stack
    # to avoid recursive function call overhead.
    stack = [None for x in range(num_converters)]
    solution = [-1 for x in range(num_bf)]
    i = 0
    while i < num_converters:
        converter_id = sorted_converters[i].converter_id
        value = 0 if stack[i] is None else stack[i][1] + 1
        schedule_map = matrix[converter_id]
        is_feasible = False
        for feasible_bf in range(value, len(schedule_map.sorted_list)):
            # Find the lowest cost non-taken schedule.
            bf_id = schedule_map.sorted_list[feasible_bf].bf_id
            # print(i, converter_id, feasible_bf, bf_id)
            if solution[bf_id] != -1:
                continue
            solution[bf_id] = converter_id
            stack[i] = bf_id, feasible_bf

            # Forward check.
            j = i + 1
            prune = False
            while j < num_converters:
                future_converter_id = sorted_converters[j].converter_id
                domain_size = matrix[
                    future_converter_id].constrain_domain(bf_id)
                if domain_size == 0:
                    # Undo constrained domains, because current
                    # value failed and it will be freed.
                    # print('No domain for {}'.format(future_converter_id))
                    while j > i:
                        matrix[sorted_converters[j]
                               .converter_id].undo_domain_constraint(bf_id)
                        j -= 1

                    prune = True
                    break
                j += 1

            if prune:
                solution[bf_id] = -1
                # print('Pruning')
                continue
            else:
                is_feasible = True
                break

        if not is_feasible:
            # No feasible value could be assigned, backtrack.
            # print('Backtracking')
            stack[i] = None
            i -= 1
            if i < 0:
                raise Exception('No feasible solution found.')
        else:
            i += 1

    return solution, matrix
