'''Program entry'''
import sys
import json
from instance import Instance


def main(argv):
    '''Main entry, argv = [command, problem instance]'''

    if len(argv) < 2:
        print('Usage: arg1=command arg2=problem instance)')
        return

    command = argv[0]
    if command == 'echo_ins':   # Parse and echo same instance for tesing
        with open(argv[1]) as file:
            problem_instance = Instance.parse(file.readlines())
            print(repr(problem_instance))
    elif command == 'parse':    # Parse problem instance
        with open(argv[1]) as file:
            problem_instance = Instance.parse(file.readlines())
            print(json.dumps(problem_instance.get_properties(),
                             indent=4, separators=(',', ': ')))
    else:
        print('Usage: arg1=command arg2=problem instance)')
        return

if __name__ == '__main__':
    main(sys.argv[1:])
