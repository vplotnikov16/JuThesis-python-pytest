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


class ClassC:
    def method_c_1(self, x: int) -> int:
        lst = [i ** 2 for i in range(x)]
        return func_c_1(lst)

    def method_c_2(self, x: int, y: int) -> int:
        # тестовое изменение ее
        return x + y
