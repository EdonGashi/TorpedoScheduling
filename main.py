'''Program entry'''
import sys
import json
import evaluator
from instance import Instance
from solution import find_initial_solution


def main(argv):
    '''Main entry, argv = [command, problem instance]'''

    if len(argv) < 2:
        print('Usage: arg1=command arg2=problem instance)')
        return

    def _get_instance():
        with open(argv[1]) as file:
            return Instance.parse(file.readlines())

    command = argv[0]
    if command == 'echo_ins':   # Parse and echo same instance for tesing
        print(repr(_get_instance()))
    elif command == 'parse':    # Parse problem instance
        print(json.dumps(_get_instance().get_properties(),
                         indent=4, separators=(',', ': ')))
    elif command == 'initial_solution':
        problem_instance = _get_instance()
        (solution, _, matrix) = find_initial_solution(problem_instance)
        print(solution)
        print('Torpedo count: %d' % 1)
        print('Desulf time: %d' %
              evaluator.calculate_desulf_time(solution, matrix))
    else:
        print('Usage: arg1=command arg2=problem instance)')
        return

if __name__ == '__main__':
    main(sys.argv[1:])
