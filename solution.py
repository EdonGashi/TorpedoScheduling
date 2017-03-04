'''Solution modeling.'''
from instance import Instance, Schedule


def find_initial_solution(instance: Instance):
    '''Finds an initial solution using forward-checking.
    The initial solution guarantees that no deadline is missed,
    but does not ensure that buffer and transit constraints are
    satisfied.
    '''
    matrix = instance.create_adjacency_matrix()
    num_bf = len(instance.bf_schedules)
    num_converters = len(instance.converter_schedules)
    # We are using an explicit preallocated stack
    # to avoid recursive function call overhead.
    stack = [None for x in range(num_converters)]
    solution = [-1 for x in range(num_bf)]
    converter_id = 0
    while converter_id < num_converters:
        value = 0 if stack[converter_id] is None else stack[converter_id][0]
        schedule_map = matrix[converter_id]
        for feasible_bf in range(value, len(schedule_map.sorted_list)):
            # Find the lowest cost non-taken schedule.
            bf_id = schedule_map.sorted_list[feasible_bf].bf_id
            if solution[bf_id] != -1:
                continue
            solution[bf_id] = converter_id
            stack[converter_id] = (bf_id, feasible_bf)

            # Forward check.
            future_id = converter_id + 1
            prune = False
            while future_id < num_converters:
                domain_size = matrix[future_id].constrain_domain(bf_id)
                if domain_size == 0:
                    # Undo constrained domains, because current
                    # value failed and it will be freed.
                    while future_id > converter_id:
                        matrix[future_id].undo_domain_constraint(bf_id)
                        future_id -= 1
                    prune = True
                    break
                future_id += 1

            if prune:
                solution[bf_id] = -1
                stack[converter_id] = None
                continue
            else:
                break

        if stack[converter_id] is None:
            # No feasible value could be assigned, backtrack.
            converter_id -= 1
            if converter_id < 0:
                raise Exception('No feasible solution found.')
        else:
            converter_id += 1

    return (solution, stack, matrix)


class _TorpedoRun:

    def __init__(self, torpedo_id, bf_id, converter_id, start_bf, end_bf,
                 start_full_buffer, start_desulf, end_desulf, start_converter,
                 end_converter, start_empty_buffer, end_empty_buffer):
        self.torpedo_id = torpedo_id
        self.bf_id = bf_id
        self.converter_id = converter_id
        self.start_bf = start_bf
        self.end_bf = end_bf
        self.start_full_buffer = start_full_buffer
        self.start_desulf = start_desulf
        self.end_resulf = end_desulf
        self.start_converter = start_converter
        self.end_converter = end_converter,
        self.start_empty_buffer = start_empty_buffer
        self.end_empty_buffer = end_empty_buffer


class _EmergencyTorpedoRun:

    def __init__(self, torpedo_id, bf_id, start_bf, end_bf, start_empty_buffer, end_empty_buffer):
        self.torpedo_id = torpedo_id
        self.bf_id = bf_id
        self.start_bf = start_bf
        self.end_bf = end_bf
        self.start_empty_buffer = start_empty_buffer
        self.end_empty_buffer = end_empty_buffer


class _Torpedo:

    def __init__(self):
        self.current_run = None


def walk_solution(instance: Instance, solution, matrix):
    schedules = []
    emergency_runs = []
    torpedoes = []

    bf_schedules = instance.bf_schedules
    converter_schedules = instance.converter_schedules

    def get_idle_torpedo(time):
        return 2, _Torpedo()

    for bf_id, converter_id in enumerate(solution):
        if converter_id == -1:
            start, end, start_bf, end_bf = instance.get_emergency_interval(
                bf_id)
            torpedo_id, torpedo = get_idle_torpedo(start)
            if torpedo.current_run is not None:
                torpedo.current_run.end_empty_buffer = start

            run = _EmergencyTorpedoRun(
                torpedo_id, bf_id, start_bf, end_bf, end, -1)
            torpedo.current_run = run
        else:
            # TODO
            pass

    latest_time = instance.get_latest_time()
    for torpedo in torpedoes:
        torpedo.current_run.end_empty_buffer = latest_time
