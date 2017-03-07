'''Solution modeling.'''
from instance import Instance
from evaluator import create_solution_timeline, calculate_conflict_count


def optimize(instance: Instance, solution, matrix, runs):
    timeline = create_solution_timeline(instance, solution, matrix)

    pass


def find_initial_solution(instance: Instance):
    '''Finds an initial solution using greedy search.
    The initial solution guarantees that no deadline is missed,
    but does not ensure that buffer and transit constraints are
    satisfied.
    '''
    matrix = instance.create_adjacency_matrix()
    num_bf = len(instance.bf_schedules)
    converters = instance.converter_schedules
    num_converters = len(instance.converter_schedules)
    sorted_converters = sorted(instance.converter_schedules,
                               key=lambda x: matrix[x.converter_id].domain_size)

    # We are using an explicit preallocated stack
    # to avoid recursive function call overhead.
    stack = [None for x in range(num_converters)]
    solution = [-1 for x in range(num_bf)]
    i = 0
    while i < num_converters:
        converter = sorted_converters[i]
        converter_id = converter.converter_id
        value = 0 if stack[i] is None else stack[i][1] + 1
        schedule_map = matrix[converter_id]
        is_feasible = False
        non_pullable = 0
        for feasible_bf in range(value, len(schedule_map.sorted_list)):
            schedule = schedule_map.sorted_list[feasible_bf]
            bf_id = schedule.bf_id
            if solution[bf_id] != -1:
                continue

            if not schedule.is_pullable:
                non_pullable += 1
                continue

            solution[bf_id] = converter_id
            stack[i] = bf_id, feasible_bf
            is_feasible = True
            break

        if not is_feasible and non_pullable > 0:
            # Trade next converter early arrival for current.
            next_converter_id = converter_id + 1
            next_converter = converters[next_converter_id]
            if next_converter.min_early_arrival > 0:
                raise Exception(
                    'Heuristic cannot serialize clusters longer than 2.')

            next_converter.min_early_arrival = next_converter.time - \
                converter.time + instance.tt_desulf_to_converter
            converter.min_early_arrival = 0

            matrix[converter_id] = instance.create_schedule_map(converter_id)
            matrix[next_converter_id] = instance.create_schedule_map(
                next_converter_id)
            continue

        if not is_feasible:
            raise Exception(
                'No feasible solution found at converter {}.'.format(converter_id))

        i += 1

    return solution, matrix
