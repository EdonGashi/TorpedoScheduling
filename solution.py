'''Solution modeling.'''
from instance import Instance


class Schedule:
    '''Models a feasible torpedo BF-Converter-Empty trip.'''

    def __init__(self,
                 start_time,
                 end_time,
                 desulf_time,
                 desulf_duration,
                 desulf_efficiency,
                 buffer_time,
                 buffer_duration):
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


class Solution:
    '''Models a solution to a problem instance.'''

    def __init__(self, instance: Instance):
        self.instance = instance

    def count_conflicts(self):
        '''Count the number of conflicts in this solution.'''

        pass

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
        return Schedule(start_time, end_time, desulf_time, desulf_duration,
                        desulf_efficiency, buffer_time, buffer_duration)

    def _create_adjacency_matrix(self):
        converter_count = len(self.instance.converter_schedules)
        bf_count = len(self.instance.bf_schedules)
        matrix = [[None for col in range(bf_count)]
                  for row in range(converter_count)]
        for i in range(converter_count):
            row = matrix[i]
            for j in range(bf_count):
                interval = self.instance.get_interval(j, i)
                row[j] = interval
