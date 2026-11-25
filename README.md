# tap-python

# Olist Data Engineering Pipeline

## Project Overview

A Python-based data engineering pipeline for processing the Olist Brazilian E-Commerce dataset.

## Objectives

- Read multiple CSV source files.
- Validate data quality and business rules.
- Apply configuration-driven transformations.
- Generate clean CSV and JSON outputs.
- Maintain execution logs and run summaries.
- Prevent duplicate processing using a manifest.

## Technologies Used

- Python 3.13
- Jupyter Notebook
- PyYAML
- Pytest
- Ruff
- Git and GitHub
- Visual Studio Code

## Environment Setup

1. Install Python and Visual Studio Code.
2. Clone the repository.
3. Open the project folder in VS Code.
4. Install the required Python packages:

   pip install pyyaml pytest ruff ipykernel

5. Create a data folder inside the project.
6. Place all nine Olist CSV files inside the data folder.
7. Verify the paths and settings in config.yaml.

## Running the Pipeline

1. Open day14.ipynb in VS Code.
2. Select the correct Python kernel.
3. Restart the kernel and run all cells.
4. Check the generated output files.
5. Review the logs and summary.json.
6. Run the pipeline again to verify duplicate processing prevention.

## Project Structure

- data/ - Raw input datasets
- output/ - Clean CSV and JSON files
- logs/ - Pipeline execution logs
- config.yaml - Pipeline configuration
- reader.py - Data extraction
- validator.py - Data validation
- transformer.py - Data transformation
- day14_pipeline.py - Pipeline execution
- day14_manifest.py - Manifest management
- manifest.json - Processed file tracking
- summary.json - Execution summary
- day15.ipynb - Final pipeline demonstration (in development)

## Data Quality Rules

- Required fields must not be empty.
- IDs must follow the expected format.
- Prices must be positive.
- Freight values must not be negative.
- Order status must contain an accepted value.
- Rejection rates must remain within the configured threshold.

## Testing

Run unit tests:

    python -m pytest -v

Run linting:

    python -m ruff check day14_pipeline.py day14_manifest.py

## Business Benefits

- Improved data quality
- Reduced manual processing
- Configurable transformations
- Traceable pipeline execution
- Prevention of duplicate processing

## Version Control

Development is managed through Git feature branches, pull requests and code reviews.
