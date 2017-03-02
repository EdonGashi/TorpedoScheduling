'''Evaluates solutions'''


def calculate_desulf_time(solution, matrix):
    '''Calculate total desulf time for a solution'''
    desulf = 0
    for (bf_id, converter_id) in enumerate(solution):
        if converter_id != -1:
            desulf += matrix[converter_id].sparse_list[bf_id].desulf_duration
    return desulf
