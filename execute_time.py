from time import time

VERY_LARGE_NUM = 999999999


def calculate_adding_as_normalMan():
    """
    add from 1 to VERY_LARGE_NUM...

    :return: msg, telling how much time it takes
    """
    result = 0
    start_time = time()
    for i in range(VERY_LARGE_NUM + 1):
        result += i
        pass
    end_time = time()
    cost_time = end_time - start_time
    print('result is ' + result.__str__())
    print('cost ' + cost_time.__str__())
    pass


def calculate_adding_as_cleverMan():
    """
    add from 1 to VERY_LARGE_NUM...

    :return: msg, telling how much time it takes
    """
    start_t = time()
    result = (1 + VERY_LARGE_NUM) * VERY_LARGE_NUM / 2
    end_t = time()
    cost_t = end_t - start_t
    print('result is ' + result.__str__())
    print('cost ' + cost_t.__str__())
    pass


if __name__ == '__main__':
    # calculate_adding_as_cleverMan()
    calculate_adding_as_normalMan()
    pass

