import pytest

from indigo.utils.math_utils import numeric_to_roman, roman_to_numeric


@pytest.mark.parametrize(
    "roman, numeric",
    [
        ("I", 1),
        ("II", 2),
        ("III", 3),
        ("IV", 4),
        ("V", 5),
        ("VI", 6),
        ("VII", 7),
        ("VIII", 8),
        ("IX", 9),
        ("X", 10),
        ("XIV", 14),
        ("XXIII", 23),
        ("XXXIX", 39),
        ("LI", 51),
        ("XCIX", 99),
        ("CIX", 109),
        ("CDXCIX", 499),
        ("DCXII", 612),
        ("CMXCIX", 999),
        ("MDXXXIV", 1534),
    ],
)
def test_roman_numeric_conversion(roman: str, numeric: int):
    assert roman_to_numeric(roman) == numeric
    assert numeric_to_roman(numeric) == roman


def test_invalid_roman_number_failure():
    with pytest.raises(ValueError) as e:
        roman_to_numeric("N")
    assert str(e.value) == "Invalid number 'N'."
