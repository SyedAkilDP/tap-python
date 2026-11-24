
import csv
import json
import logging
import math
import re
import time
from datetime import datetime
from pathlib import Path

import yaml

from day14_manifest import (
    already_processed,
    file_hash,
    load_manifest,
    save_manifest,
)

REQUIRED_FIELDS = {
    "olist_customers_dataset.csv": [
        "customer_id", "customer_unique_id"
    ],
    "olist_geolocation_dataset.csv": [
        "geolocation_zip_code_prefix",
        "geolocation_lat", "geolocation_lng"
    ],
    "olist_orders_dataset.csv": [
        "order_id", "customer_id", "order_status",
        "order_purchase_timestamp"
    ],
    "olist_order_items_dataset.csv": [
        "order_id", "product_id", "seller_id",
        "price", "freight_value", "order_item_id"
    ],
    "olist_order_payments_dataset.csv": [
        "order_id", "payment_sequential",
        "payment_type", "payment_value"
    ],
    "olist_order_reviews_dataset.csv": [
        "review_id", "order_id", "review_score"
    ],
    "olist_products_dataset.csv": ["product_id"],
    "olist_sellers_dataset.csv": ["seller_id"],
    "product_category_name_translation.csv": [
        "product_category_name",
        "product_category_name_english"
    ],
}

ALLOWED_STATUS = {
    "created", "approved", "invoiced",
    "processing", "shipped", "delivered",
    "canceled", "unavailable"
}

ID_FIELDS = {
    "order_id", "customer_id", "customer_unique_id",
    "product_id", "seller_id", "review_id"
}


def validate_row(row, required, config):
    for field in required:
        if not (row.get(field) or "").strip():
            raise ValueError(f"Missing field: {field}")

    for field, value in row.items():
        if not value:
            continue

        if field in ID_FIELDS and not re.fullmatch(r"[0-9a-fA-F]{32}", value):
            raise ValueError(f"Invalid ID: {field}")

        if field.endswith("zip_code_prefix") and not re.fullmatch(r"[0-9]{5}", value):
            raise ValueError("Invalid ZIP prefix")

        if field.endswith(("timestamp", "_date")):
            datetime.fromisoformat(value)

    if "price" in row:
        price = float(row["price"])

        if not math.isfinite(price):
            raise ValueError("Invalid price")

        if price <= config["thresholds"]["min_price"]:
            raise ValueError("Price must be positive")

        row["price"] = price

    if "freight_value" in row:
        freight = float(row["freight_value"])

        if not math.isfinite(freight) or freight < 0:
            raise ValueError("Invalid freight")

        row["freight_value"] = freight

    if "order_status" in row and row["order_status"] not in ALLOWED_STATUS:
        raise ValueError("Invalid order status")

    mappings = config["column_mappings"]

    return {
        mappings.get(key, key): value
        for key, value in row.items()
    }


def run_pipeline(config_path):
    start = time.perf_counter()
    config_path = Path(config_path)
    project = config_path.parent

    with config_path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    data_dir = project / config["paths"]["data_dir"]
    log_dir = project / config["paths"]["log_dir"]
    output_dir = project / config["paths"]["output_dir"]

    log_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    log_path = log_dir / f"pipeline_{timestamp}.log"

    logger = logging.getLogger("day14_pipeline")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = logging.FileHandler(
        log_path, encoding="utf-8"
    )

    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    ))

    logger.addHandler(handler)

    manifest_path = project / "manifest.json"
    manifest = load_manifest(manifest_path)

    summary = {
        "run_timestamp": timestamp,
        "processed_files": 0,
        "skipped_files": 0,
        "failed_files": [],
        "total_records": 0,
        "valid_records": 0,
        "rejected_records": 0,
    }

    try:
        logger.info("Pipeline started")

        for filename in config["files"]:
            source = data_dir / filename

            stem = source.stem.removeprefix("olist_")
            stem = stem.removesuffix("_dataset")

            csv_path = output_dir / f"clean_{stem}.csv"
            json_path = output_dir / f"clean_{stem}.json"

            try:
                signature = (
                    file_hash(source)
                    + ":"
                    + file_hash(config_path)
                )

                if (
                    already_processed(
                        manifest, filename, signature
                    )
                    and csv_path.is_file()
                    and json_path.is_file()
                ):
                    summary["skipped_files"] += 1
                    logger.info("SKIPPED: %s", filename)
                    continue

                clean = []
                rejected = 0
                required = REQUIRED_FIELDS[filename]

                with source.open(
                    encoding="utf-8-sig", newline=""
                ) as file:
                    reader = csv.DictReader(file)

                    if not set(required).issubset(
                        reader.fieldnames or []
                    ):
                        raise ValueError("Invalid schema")

                    for row in reader:
                        try:
                            clean.append(
                                validate_row(
                                    row, required, config
                                )
                            )
                        except (ValueError, TypeError) as error:
                            rejected += 1
                            logger.warning(
                                "%s: %s", filename, error
                            )

                total = len(clean) + rejected

                summary["total_records"] += total
                summary["valid_records"] += len(clean)
                summary["rejected_records"] += rejected

                if not total or not clean:
                    raise ValueError("No valid records")

                if rejected / total > config[
                    "thresholds"
                ]["max_rejection_rate"]:
                    raise ValueError(
                        "Rejection threshold exceeded"
                    )

                with csv_path.open(
                    "w", newline="", encoding="utf-8"
                ) as file:
                    writer = csv.DictWriter(
                        file, fieldnames=clean[0].keys()
                    )
                    writer.writeheader()
                    writer.writerows(clean)

                with json_path.open(
                    "w", encoding="utf-8"
                ) as file:
                    json.dump(clean, file, indent=4)

                manifest[filename] = signature
                save_manifest(manifest_path, manifest)

                summary["processed_files"] += 1
                logger.info("PROCESSED: %s", filename)

            except (OSError, ValueError, KeyError) as error:
                summary["failed_files"].append(filename)
                logger.error("%s: %s", filename, error)

        summary["duration_seconds"] = round(
            time.perf_counter() - start, 4
        )

        summary["status"] = (
            "FAILED"
            if summary["failed_files"]
            else "SUCCESS"
        )

        summary["log_file"] = log_path.name

        with (project / "summary.json").open(
            "w", encoding="utf-8"
        ) as file:
            json.dump(summary, file, indent=4)

        logger.info("Run summary: %s", summary)

        return summary

    finally:
        logger.removeHandler(handler)
        handler.close()
