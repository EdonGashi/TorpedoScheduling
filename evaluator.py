'''Evaluates solutions'''
from instance import Instance, Schedule


def evaluate_solution(instance: Instance, torpedo_count, desulf_time):
    '''Calculates the evaluation function for the solution parameters.'''
    return torpedo_count + desulf_time \
        / (4 * len(instance.converter_schedules) * instance.dur_desulf)


def evaluate_gain(instance: Instance, cost):
    '''Evaluates gain'''
    return len(instance.bf_schedules) + 1 - cost


def calculate_desulf_time(solution, matrix):
    '''Calculate total desulf time for a solution.'''
    desulf = 0
    for bf_id, converter_id in enumerate(solution):
        if converter_id != -1:
            desulf += matrix[converter_id].sparse_list[bf_id].desulf_duration
    return desulf


def calculate_total_time(instance: Instance, solution, matrix):
    '''Calculate total torpedo busy time for a solution.'''
    duration = 0
    for bf_id, converter_id in enumerate(solution):
        if converter_id == -1:
            duration += instance.tt_bf_emergency_pit_empty_buffer
        else:
            duration += matrix[converter_id].sparse_list[bf_id].duration
    return duration


def calculate_torpedo_count(timeline):
    '''Calculate the maximum number of torpedoes in a timeline.'''
    max_value = 0
    for slot in timeline:
        max_value = max(max_value, len(slot))
    return max_value


EMERGENCY = -1
T_EMPTY_TO_BF = 0
AT_BF = 1
T_BF_TO_FULL_BUFFER = 2
AT_FULL_BUFFER = 3
T_FULL_TO_DESULF = 4
AT_DESULF = 5
T_DESULF_TO_CONVERTER = 6
AT_CONVERTER = 7
T_CONVERTER_TO_EMPTY = 8

STATE_COUNT = 9


def create_schedule_timeline(instance: Instance, schedule: Schedule):
    '''Returns a timeline for a single schedule.'''
    timeline = [T_EMPTY_TO_BF for t in range(instance.tt_empty_buffer_to_bf)]\
        + [AT_BF for t in range(instance.dur_bf)] \
        + [T_BF_TO_FULL_BUFFER for t in range(instance.tt_bf_to_full_buffer)] \
        + [AT_FULL_BUFFER for t in range(schedule.buffer_duration)] \
        + [T_FULL_TO_DESULF for t in range(instance.tt_full_buffer_to_desulf)] \
        + [AT_DESULF for t in range(schedule.desulf_duration)] \
        + [T_DESULF_TO_CONVERTER for t in range(instance.tt_desulf_to_converter)] \
        + [AT_CONVERTER for t in range(schedule.converter_early_arrival
                                       + instance.dur_converter
                                       + schedule.converter_depart_delay)] \
        + [T_CONVERTER_TO_EMPTY for t in range(instance.tt_converter_to_empty_buffer)]
    return timeline


def get_state_constraints(instance: Instance):
    '''Returns the maximum number of each state for a time slot.'''
    max_states = [
        1,                              # T_EMPTY_TO_BF
        1,                              # AT_BF
        1,                              # T_BF_TO_FULL_BUFFER
        instance.nb_slots_full_buffer,  # AT_FULL_BUFFER
        1,                              # T_FULL_TO_DESULF
        instance.nb_slots_desulf,       # AT_DESULF
        1,                              # T_DESULF_TO_CONVERTER
        instance.nb_slots_converter,    # AT_CONVERTER
        1                               # T_CONVERTER_TO_EMPTY
    ]
    return max_states


def calculate_conflict_count(instance: Instance, timeline):
    '''Calculate total conflict count for a solution timeline.'''
    max_states = get_state_constraints(instance)
    conflicts = []
    conflict_count = 0
    max_conflicts = 0
    conflict_map = [0 for t in range(STATE_COUNT)]
    for slot, time in enumerate(timeline):
        time_conflict_count = 0
        state_counts = [0 for t in range(STATE_COUNT)]
        for _, state in time:
            if state != EMERGENCY:
                state_counts[state] += 1
        for i, state_count in enumerate(state_counts):
            if state_count > max_states[i]:
                time_conflict_count += 1
                conflict_map[i] += 1
        if time_conflict_count > 0:
            max_conflicts = max(max_conflicts, time_conflict_count)
            conflict_count += time_conflict_count
            conflicts.append((slot, time))
    return conflicts, conflict_count, max_conflicts, conflict_map


def create_solution_timeline(instance: Instance, solution, matrix):
    '''Create a timeline for each time slot of the
    instance populated with schedules from the solution.
    '''
    timeline = instance.create_timeline()
    for bf_id, converter_id in enumerate(solution):
        if converter_id == -1:
            start, end = instance.get_emergency_interval(bf_id)
            for i in range(start, end + 1):
                timeline[i].append((bf_id, EMERGENCY))
        else:
            schedule = matrix[converter_id].sparse_list[bf_id]
            schedule_timeline = create_schedule_timeline(instance, schedule)
            i = schedule.start_time
            for state in schedule_timeline:
                timeline[i].append((bf_id, state))
                i += 1
    return timeline


def serialize_schedule(instance: Instance, schedule, Schedule):
    pass
