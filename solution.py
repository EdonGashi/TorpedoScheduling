'''Solution modeling.'''


class TorpedoSchedule:
    '''Represents a blast furnace to converter schedule.'''

    def __init__(self,
                 torpedo_id,
                 bf_id,
                 converter_id,
                 start_desulf,
                 desulf_steps):
        self.torpedo_id = torpedo_id
        self.bf_id = bf_id
        self.converter_id = converter_id
        self.start_desulf = start_desulf
        self.desulf_steps = desulf_steps

    def is_valid(self, instance):
        '''Checks if the timing is valid for this schedule.'''

        pass


class TorpedoEmergencySchedule:
    '''Represents a blast furnace to emergency pit schedule.'''

    def __init__(self, torpedo_id, bf_id):
        self.torpedo_id = torpedo_id
        self.bf_id = bf_id


class Solution:
    '''Models a solution to a problem instance.'''

    def __init__(self, instance, torpedoes=0):
        self.instance = instance
        self.torpedo_schedules = []
        self.torpedoes = torpedoes

    def count_conflicts(self):
        '''Count the number of conflicts in this solution.'''

        pass
