from reader import read_csv
from validator import check_missing
from transformer import calculate_total

def test_reader(tmp_path):
    file = tmp_path / "sample.csv"
    file.write_text("order_id,price\nA001,100\n")
    assert read_csv(file) == [{"order_id": "A001", "price": "100"}]

def test_validator():
    assert check_missing("") == True
    assert check_missing("A001") == False

def test_transformer():
    assert calculate_total(500, 50) == 550