'''Provides utilities for parsing and modeling problem instances.'''
import re

PROBLEM_PROPERTIES = [
    'durBF',
    'durDesulf',
    'durConverter',
    'nbSlotsFullBuffer',
    'nbSlotsDesulf',
    'nbSlotsConverter',
    'ttBFToFullBuffer',
    'ttFullBufferToDesulf',
    'ttDesulfToConverter',
    'ttConverterToEmptyBuffer',
    'ttEmptyBufferToBF',
    'ttBFEmergencyPitEmptyBuffer'
]

BF_SCHEDULES = 'bfSchedules'
CONVERTER_SCHEDULES = 'converterSchedules'


def _camel_to_snake(name):
    '''Convert a string from camel case to snake case.'''
    expr = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', expr).lower()


class Schedule:
    '''Caches a feasible torpedo BF-Converter-Empty trip.'''

    def __init__(self,
                 bf_id,
                 converter_id,
                 start_time,
                 end_time,
                 desulf_duration,
                 desulf_efficiency,
                 buffer_duration,
                 converter_depart_delay,
                 converter_early_arrival):
        self.bf_id = bf_id
        self.converter_id = converter_id
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time
        self.desulf_duration = desulf_duration
        self.desulf_efficiency = desulf_efficiency
        self.buffer_duration = buffer_duration
        self.converter_depart_delay = converter_depart_delay
        self.converter_early_arrival = converter_early_arrival


_SORT_BIAS = [1.6, 1.4, 1.2, 1, 0.4, 0.6, 0.8, 1, 1]


def _sort_value(schedule: Schedule):
    return schedule.duration


class ScheduleMap:
    '''Caches all feasible paths for a converter schedule.'''

    def __init__(self, sparse_list):
        self.sparse_list = sparse_list
        self.sorted_list = sorted(
            [s for s in sparse_list if s is not None],
            key=_sort_value)
        self.domain_size = len(self.sorted_list)
        self.current_bf = -1

    def constrain_domain(self, bf_id):
        '''Indicate that bf_id is used somewhere else and narrow the domain.'''
        if self.sparse_list[bf_id] is not None:
            self.domain_size = max(0, self.domain_size - 1)
        return self.domain_size

    def undo_domain_constraint(self, bf_id):
        '''Indicate that bf_id is freed and expand the domain.'''
        if self.sparse_list[bf_id] is not None:
            self.domain_size += 1
        return self.domain_size


class _BFSchedule:
    '''Represents a blast furnace schedule.'''

    def __init__(self, bf_id, time, sulf_level):
        self.bf_id = bf_id
        self.time = time
        self.sulf_level = sulf_level

    def __repr__(self):
        return 'BF {} {} {}'.format(self.bf_id, self.time, self.sulf_level)


class _ConverterSchedule:
    '''Represents a converter schedule.'''

    def __init__(self, converter_id, time, depart_delay, min_early_arrival, max_sulf_level):
        self.converter_id = converter_id
        self.time = time
        self.depart_delay = depart_delay
        self.min_early_arrival = min_early_arrival
        self.max_sulf_level = max_sulf_level

    def __repr__(self):
        return 'C {} {} {}'.format(self.converter_id, self.time, self.max_sulf_level)

    def as_tuple(self):
        '''Returns a tuple for the current object values.'''
        return self.converter_id, self.time, self.depart_delay, \
            self.min_early_arrival, self.max_sulf_level


class Instance:
    '''Models a problem instance.'''

    @staticmethod
    def parse(lines):
        '''Parse string lines into a new problem instance.'''

        bf_schedules = []
        converter_schedules = []
        properties = dict()

        def parse_tuple(expr):
            '''Parse integers from string "X NUM NUM NUM".'''
            expr_list = expr.split()
            return int(expr_list[1]), int(expr_list[2]), int(expr_list[3])

        for line in lines:
            if line.startswith('BF '):      # BF NUM NUM NUM
                bf_schedules.append(parse_tuple(line))
            elif line.startswith('C '):     # C NUM NUM NUM
                converter_schedules.append(parse_tuple(line))
            elif '=' in line:               # prop=NUM
                expr_list = line.split('=')
                properties[expr_list[0]] = int(expr_list[1])

        properties[BF_SCHEDULES] = bf_schedules
        properties[CONVERTER_SCHEDULES] = converter_schedules
        return Instance(properties)

    def __init__(self, properties):
        # Init fields for static analysis.
        self.dur_bf = 0
        self.dur_desulf = 0
        self.dur_converter = 0
        self.nb_slots_full_buffer = 0
        self.nb_slots_desulf = 0
        self.nb_slots_converter = 0
        self.tt_bf_to_full_buffer = 0
        self.tt_full_buffer_to_desulf = 0
        self.tt_desulf_to_converter = 0
        self.tt_converter_to_empty_buffer = 0
        self.tt_empty_buffer_to_bf = 0
        self.tt_bf_emergency_pit_empty_buffer = 0
        props_dict = dict()
        for prop in PROBLEM_PROPERTIES + [BF_SCHEDULES, CONVERTER_SCHEDULES]:
            if prop not in properties:  # Check for missing properties
                raise Exception('Missing property %s' % prop)
            else:
                setattr(self, _camel_to_snake(prop), properties[prop])
                props_dict[prop] = properties[prop]
        self._properties = props_dict

        # Convert tuples to schedule objects
        self.bf_schedules = [_BFSchedule(*schedule_tuple)
                             for schedule_tuple in self.bf_schedules]

        self.converter_schedules = self._calculate_converter_schedules(
            self.converter_schedules)

        self.dur_emergency = self.tt_empty_buffer_to_bf + \
            self.dur_bf + self.tt_bf_emergency_pit_empty_buffer

    def _calculate_converter_schedules(self, schedules):
        converter_schedules = [None for s in schedules]
        previous_t_depart = 0
        previous_t_empty = 0
        dur = self.dur_converter
        tt_desulf_converter = self.tt_desulf_to_converter
        tt_empty = self.tt_converter_to_empty_buffer
        for converter_id, time, max_sulf_level in schedules:
            depart_delay = 0
            depart_time = time + dur
            if previous_t_empty > depart_time:
                depart_delay = previous_t_empty - depart_time
                depart_time += depart_delay

            previous_t_depart = depart_time
            previous_t_empty = depart_time + tt_empty
            converter_schedule = _ConverterSchedule(
                converter_id, time, depart_delay, 0, max_sulf_level)
            converter_schedules[converter_id] = converter_schedule

        if len(converter_schedules) == 0:
            return converter_schedules

        current_time = converter_schedules[-1].time
        for converter_id in range(len(converter_schedules) - 2, 0, -1):
            previous_schedule = converter_schedules[converter_id]
            pull = max(0, tt_desulf_converter -
                       (current_time - previous_schedule.time))
            previous_schedule.min_early_arrival = pull
            current_time = previous_schedule.time - pull

        return converter_schedules

    def get_properties(self):
        '''Returns the raw properties dictionary.'''
        return self._properties

    def get_distance(self, bf_id, converter_id):
        '''Returns a schedule for a BF-Converter pair.
        Returns None if the schedule is infeasible.
        '''
        bf = self.bf_schedules[bf_id]
        c = self.converter_schedules[converter_id]
        if c.time < bf.time:
            return None
        start_time = bf.time - self.tt_empty_buffer_to_bf
        end_time = c.time + self.dur_converter + \
            self.tt_converter_to_empty_buffer + c.depart_delay
        desulf_steps = bf.sulf_level - c.max_sulf_level
        desulf_efficiency = -desulf_steps
        desulf_duration = desulf_steps * self.dur_desulf
        if desulf_duration < 0:
            desulf_duration = 0

        buffer_time = bf.time + self.dur_bf + self.tt_bf_to_full_buffer
        desulf_overhead = self.tt_full_buffer_to_desulf \
            + desulf_duration + self.tt_desulf_to_converter
        buffer_duration = c.time - c.min_early_arrival - desulf_overhead - buffer_time
        if buffer_duration < 0:
            return None

        # early_arrival = min(buffer_duration, c.early_arrival)
        # buffer_duration -= early_arrival
        return Schedule(bf_id, converter_id, start_time, end_time, desulf_duration,
                        desulf_efficiency, buffer_duration, c.depart_delay, c.min_early_arrival)

    def create_timeline(self):
        '''Create an empty timeline for every time slot in the problem.'''
        return [[] for t in range(self.get_latest_time() + 1)]

    def get_emergency_interval(self, bf_id):
        '''Gets the timeline of an emergency
        run for the specified BF schedule.
        '''
        bf_schedule = self.bf_schedules[bf_id]
        start = bf_schedule.time - self.tt_empty_buffer_to_bf
        return start, bf_schedule.time + self.dur_bf + self.tt_bf_emergency_pit_empty_buffer, \
            bf_schedule.time, bf_schedule.time + self.dur_bf

    def create_adjacency_matrix(self):
        '''Create a cxb matrix with all feasible path costs.'''
        converter_count = len(self.converter_schedules)
        bf_count = len(self.bf_schedules)
        matrix = [None for row in range(converter_count)]
        for converter_id in range(converter_count):
            sparse_list = [None for bf in range(bf_count)]
            for bf_id in range(bf_count):
                sparse_list[bf_id] = self.get_distance(bf_id, converter_id)
            matrix[converter_id] = ScheduleMap(sparse_list)
        return matrix

    def get_latest_time(self):
        '''Returns the latest timeslot for this instance.'''
        max_converter = self.converter_schedules[-1].time \
            + self.dur_converter + self.tt_converter_to_empty_buffer
        max_emergency = self.bf_schedules[-1].time + \
            self.tt_bf_emergency_pit_empty_buffer
        return max(max_converter, max_emergency) + 1

    def __repr__(self):
        result = ''
        for prop in PROBLEM_PROPERTIES:
            result += '{}={}\n'.format(prop, self._properties[prop])
        for schedule in self.bf_schedules:
            result += repr(schedule) + '\n'
        for schedule in self.converter_schedules:
            result += repr(schedule) + '\n'
        return result
