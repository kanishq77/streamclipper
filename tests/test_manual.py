import math

import pytest

from streamclipper.manual import validate_window


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (0, 10, (0.0, 10.0)),
        ("12.3456", "20.5", (12.346, 20.5)),
    ],
)
def test_validate_window_normalizes_valid_ranges(start, end, expected):
    assert validate_window(start, end) == expected


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (-1, 2),
        (2, 2),
        (3, 2),
        ("bad", 2),
        (math.inf, 4),
        (0, 601),
    ],
)
def test_validate_window_rejects_invalid_ranges(start, end):
    with pytest.raises(Exception):
        validate_window(start, end)


def test_validate_window_honours_custom_duration_limit():
    assert validate_window(0, 900, max_duration=1000) == (0.0, 900.0)
