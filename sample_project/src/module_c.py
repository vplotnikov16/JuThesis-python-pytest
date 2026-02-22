def func_c_1(lst: list) -> int:
    return sum(lst)


def func_c_2(lst: list) -> float:
    if not lst:
        return 0.0
    return sum(lst) / len(lst)


def func_c_3(lst: list) -> int:
    if not lst:
        return 0
    return max(lst)


def func_c_4(lst: list) -> int:
    if not lst:
        return 0
    return min(lst)


def func_c_5(lst: list) -> list:
    return sorted(lst)


def func_c_6(lst: list, value: int) -> bool:
    return value in lst
