import datetime as dt
import pytest
import pandas as pd  # type: ignore
from typing import Mapping, Any, Callable

import hypothesis.strategies as st
import numpy as np
from hypothesis import given, assume, reject

import polars as pl
import polars_business as plb
from polars.type_aliases import PolarsDataType


mapping = {"Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6, "Sun": 7}
reverse_mapping = {value: key for key, value in mapping.items()}


def get_result(
    start_date: dt.date | pl.Series,
    end_date: dt.date,
    weekend: list[str],
) -> int:
    return (  # type: ignore[no-any-return]
        pl.DataFrame({"end_date": [end_date]})
        .select(n=plb.col("end_date").bdt.sub(start_date, weekend=weekend))["n"]  # type: ignore[arg-type]
        .item()
    )


@given(
    start_date=st.dates(min_value=dt.date(1000, 1, 1), max_value=dt.date(9999, 12, 31)),
    end_date=st.dates(min_value=dt.date(1000, 1, 1), max_value=dt.date(9999, 12, 31)),
    function=st.sampled_from([lambda x: x, lambda x: pl.Series([x])]),
    weekend=st.lists(
        st.sampled_from(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
        min_size=0,
        max_size=6,  # todo: fail if 7
        unique=True,
    ),
)
def test_against_np_busday_count(
    start_date: dt.date,
    end_date: dt.date,
    weekend: list[str],
    function: Callable[[dt.date], dt.date | pl.Series],
) -> None:
    result = get_result(function(start_date), end_date, weekend=weekend)
    weekmask = [0 if reverse_mapping[i] in weekend else 1 for i in range(1, 8)]
    expected = np.busday_count(start_date, end_date, weekmask=weekmask)
    assert result == expected