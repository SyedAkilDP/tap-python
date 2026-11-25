import pytest

from day14_pipeline import validate_row
from day15_errors import (
    DataQualityError,
    FileFormatError,
    SchemaError,
    check_quality,
    check_source,
)


def test_valid_source(tmp_path):
    path = tmp_path / "valid.csv"
    path.write_text("order_id\n123\n", encoding="utf-8")
    check_source(path, ["order_id"])


def test_missing_file(tmp_path):
    with pytest.raises(FileFormatError):
        check_source(tmp_path / "missing.csv", ["order_id"])


def test_invalid_schema(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_text("customer_id\n123\n", encoding="utf-8")

    with pytest.raises(SchemaError):
        check_source(path, ["order_id"])


def test_rejection_threshold():
    with pytest.raises(DataQualityError):
        check_quality(100, 30, 0.20)


def test_threshold_boundary():
    check_quality(100, 20, 0.20)


def test_column_mapping():
    record = {"price": "100", "freight_value": "20"}

    config = {
        "thresholds": {"min_price": 0},
        "column_mappings": {
            "price": "item_price",
            "freight_value": "shipping_fee",
        },
    }

    result = validate_row(
        record,
        ["price", "freight_value"],
        config,
    )

    assert result["item_price"] == 100.0
    assert result["shipping_fee"] == 20.0
    assert "price" not in result
