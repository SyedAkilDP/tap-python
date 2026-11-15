import csv
from pathlib import Path

def show_source(file_name: str) -> None:
    """Display the source file name."""
    print("Reading file:", file_name)

def read_csv(path: str | Path) -> list[dict[str, str]]:
    """Read a CSV file and return its rows as dictionaries."""
    with open(path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)