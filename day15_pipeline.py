
import csv
import json
import time
from pathlib import Path

import yaml

from day14_manifest import (
    already_processed,
    file_hash,
    load_manifest,
    save_manifest,
)
from day14_pipeline import REQUIRED_FIELDS, validate_row
from day15_errors import (
    DataQualityError,
    FileFormatError,
    SchemaError,
    check_quality,
    check_source,
)
from day15_logging import setup_logger
from reader import read_csv


def write_csv(path, records, fields):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def run_pipeline(config_path):
    start = time.perf_counter()

    config_path = Path(config_path)
    project = config_path.parent

    with config_path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    data_folder = project / config["paths"]["data_dir"]
    output_folder = project / config["paths"]["output_dir"] / "day15"
    log_folder = project / config["paths"]["log_dir"]

    output_folder.mkdir(parents=True, exist_ok=True)

    logger, log_path = setup_logger(log_folder)

    manifest_path = output_folder / "manifest.json"
    manifest = load_manifest(manifest_path)

    bad_records = []

    bad_fields = [
        "source_file",
        "record_number",
        "rejection_reason",
        "raw_record",
    ]

    summary = {
        "processed_files": 0,
        "skipped_files": 0,
        "failed_files": {},
        "total_records": 0,
        "valid_records": 0,
        "rejected_records": 0,
    }

    try:
        logger.info("Day 15 pipeline started")

        for filename in config["files"]:
            source = data_folder / filename

            csv_path = output_folder / f"clean_{source.stem}.csv"
            json_path = output_folder / f"clean_{source.stem}.json"
            rejected_path = output_folder / f"bad_{source.stem}.csv"

            try:
                check_source(source, (config.get("required_fields", {}).get(filename) or REQUIRED_FIELDS[filename]))

                signature = (
                    file_hash(source) + ":" + file_hash(config_path)
                )

                if (
                    already_processed(manifest, filename, signature)
                    and csv_path.exists()
                    and json_path.exists()
                    and rejected_path.exists()
                ):
                    with rejected_path.open(
                        encoding="utf-8", newline=""
                    ) as file:
                        bad_records.extend(csv.DictReader(file))

                    summary["skipped_files"] += 1
                    logger.info("SKIPPED: %s", filename)
                    continue

                manifest.pop(filename, None)
                save_manifest(manifest_path, manifest)

                records = read_csv(str(source))

                valid = []
                rejected = []

                for row_number, record in enumerate(records, start=1):
                    try:
                        if None in record:
                            raise ValueError("Malformed CSV record")

                        clean = validate_row(
                            record.copy(),
                            (config.get("required_fields", {}).get(filename) or REQUIRED_FIELDS[filename]),
                            config,
                        )

                        valid.append(clean)

                    except (ValueError, TypeError) as error:
                        rejected.append({
                            "source_file": filename,
                            "record_number": row_number,
                            "rejection_reason": str(error),
                            "raw_record": json.dumps(
                                record, default=str
                            ),
                        })

                bad_records.extend(rejected)

                write_csv(rejected_path, rejected, bad_fields)

                summary["total_records"] += len(records)
                summary["valid_records"] += len(valid)
                summary["rejected_records"] += len(rejected)

                if rejected:
                    logger.warning(
                        "%s | Rejected: %s",
                        filename,
                        len(rejected),
                    )

                check_quality(
                    len(records),
                    len(rejected),
                    config["thresholds"]["max_rejection_rate"],
                )

                write_csv(csv_path, valid, list(valid[0].keys()))

                with json_path.open("w", encoding="utf-8") as file:
                    json.dump(valid, file, indent=4, default=str)

                manifest[filename] = signature
                save_manifest(manifest_path, manifest)

                summary["processed_files"] += 1

                logger.info("PROCESSED: %s", filename)

            except (
                SchemaError,
                FileFormatError,
                DataQualityError,
                OSError,
                ValueError,
                KeyError,
                csv.Error,
            ) as error:
                summary["failed_files"][filename] = str(error)
                logger.error("FAILED: %s | %s", filename, error)

        write_csv(
            output_folder / "bad_records.csv",
            bad_records,
            bad_fields,
        )

        summary["duration_seconds"] = round(
            time.perf_counter() - start, 4
        )

        summary["status"] = (
            "FAILED" if summary["failed_files"] else "SUCCESS"
        )

        summary["log_file"] = log_path.name

        with (output_folder / "summary.json").open(
            "w", encoding="utf-8"
        ) as file:
            json.dump(summary, file, indent=4)

        logger.info("Pipeline summary: %s", summary)

        return summary

    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
