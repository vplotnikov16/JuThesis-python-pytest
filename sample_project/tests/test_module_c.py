import time
from src.module_c import func_c_1, func_c_2, func_c_3, func_c_4, func_c_5, func_c_6


def test_func_c_1_sum():
    time.sleep(0.11)
    assert func_c_1([1, 2, 3]) == 6
    assert func_c_1([]) == 0
    assert func_c_1([10]) == 10


def test_func_c_2_average():
    time.sleep(0.13)
    assert func_c_2([1, 2, 3, 4]) == 2.5
    assert func_c_2([10]) == 10.0
    assert func_c_2([]) == 0.0


def test_func_c_3_max():
    time.sleep(0.07)
    assert func_c_3([1, 5, 3]) == 5
    assert func_c_3([10]) == 10
    assert func_c_3([]) == 0


def test_func_c_4_min():
    time.sleep(0.08)
    assert func_c_4([1, 5, 3]) == 1
    assert func_c_4([10]) == 10
    assert func_c_4([]) == 0


def test_func_c_5_sort():
    time.sleep(0.16)
    assert func_c_5([3, 1, 2]) == [1, 2, 3]
    assert func_c_5([]) == []
    assert func_c_5([5, 5, 5]) == [5, 5, 5]


def test_func_c_6_contains():
    time.sleep(0.05)
    assert func_c_6([1, 2, 3], 2) is True
    assert func_c_6([1, 2, 3], 5) is False
    assert func_c_6([], 1) is False


def test_combined_c_1_and_c_2():
    time.sleep(0.2)
    lst = [10, 20, 30]
    total = func_c_1(lst)
    assert total == 60
    avg = func_c_2(lst)
    assert avg == 20.0


def test_combined_c_3_and_c_4():
    time.sleep(0.17)
    lst = [5, 10, 2, 8]
    max_val = func_c_3(lst)
    min_val = func_c_4(lst)
    assert max_val == 10
    assert min_val == 2


def test_combined_c_5_and_c_6():
    time.sleep(0.24)
    lst = [3, 1, 4, 1, 5]
    sorted_lst = func_c_5(lst)
    assert sorted_lst == [1, 1, 3, 4, 5]
    assert func_c_6(sorted_lst, 3) is True
    assert func_c_6(sorted_lst, 2) is False


def test_statistics_pipeline():
    time.sleep(0.4)
    data = [15, 22, 8, 19, 3, 11]

    total = func_c_1(data)
    assert total == 78

    avg = func_c_2(data)
    assert avg == 13.0

    max_val = func_c_3(data)
    assert max_val == 22

    min_val = func_c_4(data)
    assert min_val == 3

    sorted_data = func_c_5(data)
    assert sorted_data == [3, 8, 11, 15, 19, 22]

    assert func_c_6(sorted_data, 11) is True
