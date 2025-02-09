import re

from indigo.models.patterns import RE_ROMAN_NUMBER_PATTERN

ROMAN_TO_NUMERIC = {
    "I": 1,
    "IV": 4,
    "V": 5,
    "IX": 9,
    "X": 10,
    "XL": 40,
    "L": 50,
    "XC": 90,
    "C": 100,
    "CD": 400,
    "D": 500,
    "CM": 900,
    "M": 1000,
}

ROMAN = list(ROMAN_TO_NUMERIC.keys())
NUMERIC = list(ROMAN_TO_NUMERIC.values())


def roman_to_numeric(number: str) -> int:
    if not re.match(rf"^{RE_ROMAN_NUMBER_PATTERN}$", number):
        raise ValueError(f"Invalid number {number!r}.")
    numeric_number = 0
    index = 0
    while index < len(number):
        if (
            index + 1 < len(number)
            and number[index : index + 2] in ROMAN_TO_NUMERIC
        ):
            numeric_number += ROMAN_TO_NUMERIC[number[index : index + 2]]
            index += 2
        else:
            numeric_number += ROMAN_TO_NUMERIC[number[index]]
            index += 1
    return numeric_number


def numeric_to_roman(number: int) -> str:
    roman_number = ""
    counter = len(ROMAN_TO_NUMERIC) - 1
    while number:
        div = number // NUMERIC[counter]
        number %= NUMERIC[counter]
        while div:
            roman_number += ROMAN[counter]
            div -= 1
        counter -= 1
    return roman_number
