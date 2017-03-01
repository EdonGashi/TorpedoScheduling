'''Solution modeling.'''
from instance import Instance

class Solution:
    '''Models a solution to a problem instance.'''
    
    def __init__(self, instance: Instance):
        self.instance = instance
