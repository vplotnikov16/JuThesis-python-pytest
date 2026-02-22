import time
from src.module_b import func_b_1, func_b_2, func_b_3, func_b_4, func_b_5


def test_func_b_1_upper():
    time.sleep(0.08)
    assert func_b_1("hello") == "HELLO"
    assert func_b_1("WORLD") == "WORLD"


def test_func_b_2_lower():
    time.sleep(0.06)
    assert func_b_2("HELLO") == "hello"
    assert func_b_2("world") == "world"


def test_func_b_3_reverse():
    time.sleep(0.1)
    assert func_b_3("hello") == "olleh"
    assert func_b_3("abc") == "cba"


def test_func_b_4_length():
    time.sleep(0.04)
    assert func_b_4("hello") == 5
    assert func_b_4("") == 0
    assert func_b_4("a") == 1


def test_func_b_5_count():
    time.sleep(0.09)
    assert func_b_5("hello", "l") == 2
    assert func_b_5("world", "o") == 1
    assert func_b_5("test", "z") == 0


def test_combined_b_1_and_b_3():
    time.sleep(0.22)
    upper = func_b_1("test")
    reversed_upper = func_b_3(upper)
    assert reversed_upper == "TSET"


def test_combined_b_2_and_b_4():
    time.sleep(0.14)
    lower = func_b_2("HELLO")
    length = func_b_4(lower)
    assert length == 5


def test_all_string_ops():
    time.sleep(0.35)
    text = "Python"
    upper = func_b_1(text)
    assert upper == "PYTHON"
    lower = func_b_2(upper)
    assert lower == "python"
    reversed_text = func_b_3(lower)
    assert reversed_text == "nohtyp"
    length = func_b_4(reversed_text)
    assert length == 6
    count_n = func_b_5(reversed_text, "n")
    assert count_n == 1
