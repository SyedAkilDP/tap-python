import csv
from pathlib import Path


class SchemaError(Exception):
    pass


class FileFormatError(Exception):
    pass


class DataQualityError(Exception):
    pass


def check_source(path, required_fields):
    path = Path(path)

    if not path.is_file():
        raise FileFormatError(f"Missing file: {path.name}")

    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                raise FileFormatError("Empty file")

            missing = set(required_fields) - set(reader.fieldnames)

            if missing:
                raise SchemaError(f"Missing columns: {sorted(missing)}")

            if next(reader, None) is None:
                raise FileFormatError("No data records")

    except (OSError, UnicodeError, csv.Error) as error:
        raise FileFormatError(str(error)) from error


def check_quality(total, rejected, threshold):
    if total == 0:
        raise DataQualityError("No records available")

    if rejected == total:
        raise DataQualityError("No valid records available")

    rejection_rate = rejected / total

    if rejection_rate > threshold:
        raise DataQualityError(
            f"Rejection rate {rejection_rate:.2%} "
            f"exceeds threshold {threshold:.2%}"
        )
