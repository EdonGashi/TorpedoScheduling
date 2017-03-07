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
            duration += instance.dur_emergency
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


def create_emergency_timeline(instance: Instance, bf_id):
    '''Returns a timeline for a single emergency schedule.'''
    start, end, start_bf, end_bf = instance.get_emergency_interval(bf_id)
    return start, [T_EMPTY_TO_BF for t in range(start, start_bf)] \
        + [AT_BF for t in range(start_bf, end_bf)] \
        + [EMERGENCY for t in range(end_bf, end)]


def create_schedule_timeline(instance: Instance, schedule: Schedule):
    '''Returns a timeline for a single schedule.'''
    timeline = [T_EMPTY_TO_BF for t in range(instance.tt_empty_buffer_to_bf)] \
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


def calculate_conflict_count(instance: Instance, timeline, start=0, end=-1):
    '''Calculate total conflict count for a solution timeline.'''
    max_states = get_state_constraints(instance)
    conflicts = []
    conflict_count = 0
    max_conflicts = 0
    conflict_map = [0 for t in range(STATE_COUNT)]
    if end < 0:
        end = len(timeline)
    for slot in range(start, end):
        time = timeline[slot]
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
            start_time, schedule_timeline = create_emergency_timeline(
                instance, bf_id)
            i = start_time
            for state in schedule_timeline:
                timeline[i].append((bf_id, state))
                i += 1
        else:
            schedule = matrix[converter_id].sparse_list[bf_id]
            schedule_timeline = create_schedule_timeline(instance, schedule)
            i = schedule.start_time
            for state in schedule_timeline:
                timeline[i].append((bf_id, state))
                i += 1
    return timeline


class _TorpedoRun:

    @staticmethod
    def compile(instance: Instance, schedule: Schedule, torpedo_id):
        '''Calculates each step of a torpedo run.'''
        bf = instance.bf_schedules[schedule.bf_id]
        start_bf = bf.time
        end_bf = bf.time + instance.dur_bf
        start_full_buffer = end_bf + instance.tt_bf_to_full_buffer
        end_full_buffer = start_full_buffer + schedule.buffer_duration
        start_desulf = end_full_buffer + instance.tt_full_buffer_to_desulf
        end_desulf = start_desulf + schedule.desulf_duration
        start_converter = end_desulf + instance.tt_desulf_to_converter
        end_converter = schedule.converter_early_arrival + start_converter \
            + instance.dur_converter + schedule.converter_depart_delay
        start_empty_buffer = end_converter + instance.tt_converter_to_empty_buffer
        return _TorpedoRun(torpedo_id, schedule.bf_id, schedule.converter_id, start_bf,
                           end_bf, start_full_buffer, end_full_buffer, start_desulf,
                           end_desulf, start_converter, end_converter, start_empty_buffer, -1)

    def __init__(self, torpedo_id, bf_id, converter_id, start_bf, end_bf,
                 start_full_buffer, end_full_buffer, start_desulf, end_desulf,
                 start_converter, end_converter, start_empty_buffer, end_empty_buffer):
        self.torpedo_id = torpedo_id
        self.bf_id = bf_id
        self.converter_id = converter_id
        self.start_bf = start_bf
        self.end_bf = end_bf
        self.start_full_buffer = start_full_buffer
        self.end_full_buffer = end_full_buffer
        self.start_desulf = start_desulf
        self.end_desulf = end_desulf
        self.start_converter = start_converter
        self.end_converter = end_converter
        self.start_empty_buffer = start_empty_buffer
        self.end_empty_buffer = end_empty_buffer

    def __repr__(self):
        return 'idTorpedo={}\nidBF={}\nidConverter={}\nstartBF={}\nendBF={}\nstartFullBuffer={}\nendFullBuffer={}\nstartDesulf={}\nendDesulf={}\nstartConverter={}\nendConverter={}\nstartEmptyBuffer={}\nendEmptyBuffer={}\n' \
            .format(self.torpedo_id, self.bf_id, self.converter_id, self.start_bf, self.end_bf,
                    self.start_full_buffer, self.end_full_buffer, self.start_desulf, self.end_desulf,
                    self.start_converter, self.end_converter, self.start_empty_buffer, self.end_empty_buffer)


class _EmergencyTorpedoRun:

    def __init__(self, torpedo_id, bf_id, start_bf, end_bf, start_empty_buffer, end_empty_buffer):
        self.torpedo_id = torpedo_id
        self.bf_id = bf_id
        self.start_bf = start_bf
        self.end_bf = end_bf
        self.start_empty_buffer = start_empty_buffer
        self.end_empty_buffer = end_empty_buffer

    def __repr__(self):
        return 'idTorpedo={}\nidBF={}\nidConverter=-1\nstartBF={}\nendBF={}\nstartEmptyBuffer={}\nendEmptyBuffer={}\n' \
            .format(self.torpedo_id, self.bf_id, self.start_bf,
                    self.end_bf, self.start_empty_buffer, self.end_empty_buffer)


class _Torpedo:

    def __init__(self, torpedo_id):
        self.torpedo_id = torpedo_id
        self.current_run = None


def calculate_solution_runs(instance: Instance, solution, matrix):
    '''Calculates the timeline for every schedule in the solution.'''
    runs = []
    torpedoes = []

    def _get_idle_torpedo(time):
        for torpedo in torpedoes:
            if time >= torpedo.current_run.start_empty_buffer:
                return torpedo
        torpedo = _Torpedo(len(torpedoes))
        torpedoes.append(torpedo)
        return torpedo

    for bf_id, converter_id in enumerate(solution):
        if converter_id == -1:
            start, end, start_bf, end_bf = instance.get_emergency_interval(
                bf_id)
            torpedo = _get_idle_torpedo(start)
            if torpedo.current_run is not None:
                torpedo.current_run.end_empty_buffer = start

            run = _EmergencyTorpedoRun(
                torpedo.torpedo_id, bf_id, start_bf, end_bf, end, -1)
            torpedo.current_run = run
            runs.append(run)
        else:
            schedule = matrix[converter_id].sparse_list[bf_id]
            start = schedule.start_time
            torpedo = _get_idle_torpedo(start)
            if torpedo.current_run is not None:
                torpedo.current_run.end_empty_buffer = start
            run = _TorpedoRun.compile(instance, schedule, torpedo.torpedo_id)
            torpedo.current_run = run
            runs.append(run)

    latest_time = instance.get_latest_time()
    for torpedo in torpedoes:
        torpedo.current_run.end_empty_buffer = latest_time

    return runs, torpedoes
