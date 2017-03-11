'''Solution modeling.'''
from instance import Instance
from evaluator import *


def resolve_conflicts(instance: Instance, solution, matrix):
    '''Attempt to resolve full buffer to desulf conflicts.'''
    timeline = create_solution_timeline(instance, solution, matrix)
    length = len(timeline)
    i = 0
    current_count = 0
    current_bf = -1
    while i < length:
        slot = timeline[i]
        in_transit = [t[0] for t in slot if t[1] == T_FULL_TO_DESULF]
        count_in_transit = len(in_transit)
        if count_in_transit > 2:
            raise Exception(
                'Cannot resolve more than two simultaneous transits.')
        elif count_in_transit == 2:
            delta = instance.tt_full_buffer_to_desulf - current_count
            current_schedule = matrix[
                solution[current_bf]].get_current_schedule()
            if current_schedule.buffer_duration >= delta:
                current_schedule.buffer_duration -= delta
                current_schedule.converter_early_arrival += delta
            else:
                new_bf = in_transit[1] if in_transit[
                    1] != current_bf else in_transit[0]
                next_schedule = matrix[solution[new_bf]].get_current_schedule()
                new_delta = instance.tt_full_buffer_to_desulf + delta
                if next_schedule.buffer_duration >= new_delta:
                    next_schedule.buffer_duration -= new_delta
                    next_schedule.converter_early_arrival += new_delta
                else:
                    raise Exception(
                        'Cannot resolve transit conflicts for current configuration.')

            i += delta
            current_bf = -1
            current_count = 0
            continue
        elif count_in_transit == 1:
            current_bf = in_transit[0]
            current_count += 1
        else:
            current_bf = -1
            current_count = 0

        i += 1


class ConflictTimeline:
    '''Maintains and mutates a conflict timeline.'''

    @staticmethod
    def create(instance: Instance, solution, matrix):
        '''Create a timeline with state distribution
        for each time slot of the instance.
        '''
        timeline = timeline = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                               for t in range(instance.get_latest_time() + 1)]
        for bf_id, converter_id in enumerate(solution):
            if converter_id == -1:
                start_time, schedule_timeline \
                    = create_emergency_timeline(instance, bf_id)
                i = start_time
                for state in schedule_timeline:
                    timeline[i][state] += 1
                    i += 1
            else:
                schedule = matrix[converter_id].sparse_list[bf_id]
                schedule_timeline \
                    = create_schedule_timeline(instance, schedule)
                i = schedule.start_time
                for state in schedule_timeline:
                    timeline[i][state] += 1
                    i += 1
        return ConflictTimeline(instance, timeline)

    def __init__(self, instance: Instance, timeline):
        self.instance = instance
        self.timeline = timeline
        self.max_states = get_state_constraints(instance)

    def count_conflicts(self, start=0, end=-1):
        '''Calculate conflict distribution and torpedo count for a timeline.'''
        timeline = self.timeline
        max_states = self.max_states
        max_torpedoes = 0
        conflict_map = [0 for t in range(STATE_COUNT)]
        if end < 0:
            end = len(timeline)
        for slot in range(start, end):
            time = timeline[slot]
            max_torpedoes = max(max_torpedoes, sum(time))
            for i, max_state in enumerate(max_states):
                if time[i] > max_state:
                    conflict_map[i] += 1
        return conflict_map, max_torpedoes

    def add(self, time, state_list):
        timeline = self.timeline
        for state in state_list:
            timeline[time][state] += 1
            time += 1

    def subtract(self, time, state_list):
        timeline = self.timeline
        for state in state_list:
            timeline[time][state] -= 1
            time += 1


def hill_climb(instance: Instance, solution, matrix, max_lookahead=32):
    '''Minimizes desulf duration without causing new conflicts.'''
    timeline = ConflictTimeline.create(instance, solution, matrix)

    def _is_feasible(conflict_map, new_conflict_map, max_torpedoes, new_max_torpedoes):
        if new_max_torpedoes > max_torpedoes:
            return False
        for i, state in enumerate(new_conflict_map):
            if state > conflict_map[i]:
                return False
        return True

    def _try_update_timeline(c1, tc1, n1, tn1, c2, tc2, n2, tn2):
        ec1, en1, ec2, en2 = tc1 + \
            len(c1), tn1 + len(n1), tc2 + len(c2), tn2 + len(n2)

        def _count_conflicts():
            return [timeline.count_conflicts(tc1, ec1),
                    timeline.count_conflicts(tn1, en1),
                    timeline.count_conflicts(tc2, ec2),
                    timeline.count_conflicts(tn2, en2)]

        state_before = _count_conflicts()
        timeline.subtract(tc1, c1)
        timeline.subtract(tc2, c2)
        timeline.add(tn1, n1)
        timeline.add(tn2, n2)
        state_after = _count_conflicts()

        def _check_feasibility():
            for i, (new_conflicts, new_torpedoes) in enumerate(state_after):
                conflicts, torpedoes = state_before[i]
                if not _is_feasible(conflicts, new_conflicts, torpedoes, new_torpedoes):
                    return False
            return True

        if _check_feasibility():
            return True
        else:
            timeline.add(tc1, c1)
            timeline.add(tc2, c2)
            timeline.subtract(tn1, n1)
            timeline.subtract(tn2, n2)
            return False

    def _try_swap_emergency(curr1, new1):
        c1 = create_schedule_timeline(instance, curr1)
        n1 = create_schedule_timeline(instance, new1)
        tc2, c2 = create_emergency_timeline(instance, new1.bf_id)
        tn2, n2 = create_emergency_timeline(instance, curr1.bf_id)
        if _try_update_timeline(c1, curr1.start_time, n1, new1.start_time,
                                c2, tc2, n2, tn2):
            solution[curr1.bf_id] = -1
            solution[new1.bf_id] = curr1.converter_id
            return True
        else:
            return False

    def _try_swap(curr1, new1):
        if curr1 is new1 or not new1.is_pullable:
            return False

        gain1 = curr1.desulf_duration - new1.desulf_duration
        converter1 = curr1.converter_id
        converter2 = solution[new1.bf_id]
        schedule_map2 = matrix[converter2]
        if converter2 == -1:
            if gain1 <= 0:
                return False
            return _try_swap_emergency(curr1, new1)

        new2 = schedule_map2.sparse_list[curr1.bf_id]
        if new2 is None or not new2.is_pullable:
            return False

        curr2 = schedule_map2.sparse_list[new1.bf_id]
        gain2 = curr2.desulf_duration - new2.desulf_duration
        if gain1 + gain2 <= 0:
            return False

        c1 = create_schedule_timeline(instance, curr1)
        n1 = create_schedule_timeline(instance, new1)
        c2 = create_schedule_timeline(instance, curr2)
        n2 = create_schedule_timeline(instance, new2)
        if _try_update_timeline(c1, curr1.start_time, n1, new1.start_time,
                                c2, curr2.start_time, n2, new2.start_time):
            solution[curr1.bf_id] = converter2
            solution[new1.bf_id] = converter1
            schedule_map2.current_index = new2.index
            return True
        else:
            return False

    lookahead = 1
    max_lookahead = min(len(instance.bf_schedules) - 1, max_lookahead)
    loop = True
    while loop:
        while True:
            updates = 0
            for schedule_map in matrix:
                domain = schedule_map.sorted_list
                domain_size = len(domain)
                current_index = schedule_map.current_index
                current_schedule = domain[current_index]
                for index in range(current_index + 1,
                                   min(domain_size, current_index + 1 + lookahead)):
                    schedule = domain[index]
                    if _try_swap(current_schedule, schedule):
                        schedule_map.current_index = index
                        updates += 1
                        break

            if updates == 0:
                break

        if lookahead == max_lookahead:
            loop = False
        lookahead *= 2
        if lookahead > max_lookahead:
            lookahead = max_lookahead
    return timeline


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
            schedule_map.current_index = feasible_bf
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
            solution[stack[i - 1][0]] = -1
            stack[i - 1] = None
            i -= 1
            continue
        elif not is_feasible:
            raise Exception(
                'No feasible solution found at converter {}.'.format(converter_id))

        i += 1
    return solution, matrix
