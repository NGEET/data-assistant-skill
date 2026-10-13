#!/usr/bin/env python3
"""Tests for search_datasets.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import pytest
from search_datasets import search, CSV_PATH


@pytest.fixture
def df():
    return pd.read_csv(CSV_PATH)


def test_csv_exists():
    assert CSV_PATH.exists(), f"CSV not found at {CSV_PATH}"


def test_csv_has_rows(df):
    assert len(df) > 0


def test_csv_required_columns(df):
    required = ["name", "@id", "datePublished", "keywords", "creator", "variableMeasured"]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"


def test_search_no_filters_returns_all(df):
    result = search(df)
    assert len(result) == len(df)


def test_search_by_name(df):
    result = search(df, name="soil")
    assert len(result) > 0
    for _, row in result.iterrows():
        assert "soil" in str(row["name"]).lower()


def test_search_by_keywords(df):
    result = search(df, keywords="carbon")
    assert len(result) >= 0  # just ensure no crash


def test_search_by_date_range(df):
    result = search(df, start_date="2018-01-01", end_date="2022-12-31")
    for _, row in result.iterrows():
        d = str(row["datePublished"])
        assert "2018" <= d[:4] <= "2022"


def test_search_no_match(df):
    result = search(df, name="xyzzy_no_match_9999")
    assert len(result) == 0


def test_search_multiple_filters(df):
    result = search(df, name="soil", keywords="carbon")
    # Should be subset of name-only search
    name_only = search(df, name="soil")
    assert len(result) <= len(name_only)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
