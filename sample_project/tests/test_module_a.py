import time
from src.module_a import func_a_1, func_a_2, func_a_3, func_a_4


def test_func_a_1_basic():
    time.sleep(0.1)  # Имитация работы
    assert func_a_1(2, 3) == 5
    assert func_a_1(0, 0) == 0
    assert func_a_1(-1, 1) == 0


def test_func_a_1_negative():
    time.sleep(0.15)
    assert func_a_1(-5, -3) == -8
    assert func_a_1(-10, 5) == -5


def test_func_a_2_basic():
    time.sleep(0.2)
    assert func_a_2(5, 3) == 2
    assert func_a_2(10, 10) == 0


def test_func_a_3_double():
    time.sleep(0.05)
    assert func_a_3(5) == 10
    assert func_a_3(0) == 0
    assert func_a_3(-3) == -6


def test_func_a_4_even():
    time.sleep(0.12)
    assert func_a_4(2) is True
    assert func_a_4(4) is True
    assert func_a_4(3) is False
    assert func_a_4(0) is True


def test_combined_a_1_and_a_2():
    time.sleep(0.25)
    result = func_a_1(10, 5)
    assert result == 15
    result2 = func_a_2(result, 5)
    assert result2 == 10


def test_combined_a_3_and_a_4():
    time.sleep(0.18)
    doubled = func_a_3(7)
    assert doubled == 14
    assert func_a_4(doubled) is True
