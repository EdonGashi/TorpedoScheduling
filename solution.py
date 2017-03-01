'''Solution modeling.'''
from operator import attrgetter
from instance import Instance


class Schedule:
    '''Caches a feasible torpedo BF-Converter-Empty trip.'''

    def __init__(self,
                 bf_id,
                 converter_id,
                 start_time,
                 end_time,
                 desulf_time,
                 desulf_duration,
                 desulf_efficiency,
                 buffer_time,
                 buffer_duration):
        self.bf_id = bf_id
        self.converter_id = converter_id
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time + 1
        self.desulf_time = desulf_time
        self.desulf_duration = desulf_duration
        self.desulf_efficiency = desulf_efficiency
        self.buffer_time = buffer_time
        self.buffer_duration = buffer_duration

    def simulate(self, instance):
        for t in range(self.start_time, self.end_time + 1):

            pass
        pass


class ScheduleMap:
    '''Caches all feasible paths for a converter schedule.'''

    def __init__(self, sparse_list):
        self.sparse_list = sparse_list
        self.sorted_list = sorted([s for s in sparse_list if s is not None],
                                  key=attrgetter('duration', 'desulf_efficiency'))
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
            self.domain_size = self.domain_size + 1
        return self.domain_size


class Solution:
    '''Models a solution to a problem instance.'''

    def __init__(self, instance: Instance):
        self.instance = instance

    def get_distance(self, bf_id, converter_id):
        '''Returns a schedule for a BF-Converter pair.
        Returns None if the schedule is infeasible.
        '''
        instance = self.instance
        bf = instance.bf_schedules[bf_id]
        c = instance.converter_schedules[converter_id]
        if c.time < bf.time:
            return None
        start_time = bf.time - instance.tt_empty_buffer_to_bf
        end_time = c.time + instance.dur_converter + \
            instance.tt_converter_to_empty_buffer
        desulf_steps = bf.sulf_level - c.max_sulf_level
        desulf_duration = desulf_steps * instance.dur_desulf
        desulf_efficiency = -desulf_duration
        if desulf_duration < 0:
            desulf_duration = 0

        buffer_time = bf.time + instance.dur_bf + instance.tt_bf_to_full_buffer
        desulf_overhead = instance.tt_full_buffer_to_desulf \
            + desulf_duration + instance.tt_desulf_to_converter
        buffer_duration = c.time - desulf_overhead - buffer_time
        if buffer_duration < 0:
            return None
        desulf_time = buffer_time + buffer_duration + instance.tt_full_buffer_to_desulf
        return Schedule(bf_id, converter_id, start_time, end_time, desulf_time,
                        desulf_duration, desulf_efficiency, buffer_time, buffer_duration)

    def create_timeline(self):
        '''Create an empty timeline for every time slot in the problem.'''
        return [None for t in range(self.instance.get_latest_time() + 1)]

    def create_adjacency_matrix(self):
        '''Create a cxb matrix with all feasible path costs.'''
        converter_count = len(self.instance.converter_schedules)
        bf_count = len(self.instance.bf_schedules)
        matrix = [None for row in range(converter_count)]
        for converter_id in range(converter_count):
            sparse_list = [None for bf in range(bf_count)]
            for bf_id in range(bf_count):
                sparse_list[bf_id] = self.get_distance(bf_id, converter_id)
            matrix[converter_id] = ScheduleMap(sparse_list)
        return matrix
