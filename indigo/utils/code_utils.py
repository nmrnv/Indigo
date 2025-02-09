Index = int


def next_index(current: Index, arr_length: int):
    return current + 1 if current + 1 < arr_length else 0
