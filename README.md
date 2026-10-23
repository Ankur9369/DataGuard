# DataGuard --- Data Quality Monitoring & Anomaly Detection

DataGuard is a B.Tech CSE mini project built with Python and Streamlit.
It helps users compare a source dataset with a target dataset, identify
common data-quality issues, and export validation results.

> **Data privacy:** Use synthetic, public, or otherwise authorized
> datasets only. Do not upload confidential company, client, or personal
> data.

## Features

-   Upload source and target datasets in CSV or XLSX format.
-   Validate input files and report common loading errors.
-   Compare record counts, column counts, missing values, and duplicate
    rows.
-   Compare schema, including missing/extra columns and shared-column
    data types.
-   Analyze missing values by column in both datasets.
-   Detect duplicate records.
-   Reconcile source and target records using a selected shared key,
    when the key is unique and non-missing in both datasets.
-   Compare shared records at field level and show mismatched values.
-   Configure a numeric minimum and maximum and flag target rows outside
    the selected range.
-   Explore uploaded datasets and download a selected dataset as CSV.
-   View validation status and a data-quality score.
-   Download validation results, failed numeric records, schema
    comparison, and a multi-sheet Excel report.
-   Save validation runs to a local SQLite database and view score
    history.

## Technology stack

-   **Python** --- application logic
-   **Streamlit** --- interactive web interface
-   **Pandas** --- tabular data processing
-   **Plotly** --- visualizations
-   **SQLite** --- local validation history
-   **OpenPyXL** --- Excel report export

## Project structure

``` text
DataGuard/
├── app.py
├── requirements.txt
└── dataguard_history.db   # created automatically when history is saved
```

The SQLite database is generated at runtime in the working directory
when the app initializes its history table.

## Requirements

-   Python 3.10 or newer recommended
-   pip
-   A web browser

## Setup on Windows (VS Code / PowerShell)

Open a terminal in your project directory.

### 1. Create and activate a virtual environment

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the app using the
environment's Python executable directly:

``` powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### 2. Install dependencies

Create a `requirements.txt` file with:

``` text
streamlit
pandas
plotly
openpyxl
```

Then install:

``` powershell
python -m pip install -r requirements.txt
```

SQLite support is included with Python's standard library; no separate
package is needed.

### 3. Run DataGuard

``` powershell
streamlit run app.py
```

Streamlit will print a local URL in the terminal. Open that URL in your
browser.

## How to use

1.  Prepare two authorized CSV or XLSX files: a source dataset and a
    target dataset.
2.  Upload both files.
3.  Review the dataset overview and comparison.
4.  Inspect schema, missing values, and duplicates.
5.  Select a shared unique key for source-to-target reconciliation.
6.  Optionally configure a numeric range rule for a target column.
7.  Review the validation report, score, and failed rows.
8.  Download the CSV or Excel reports you need.
9.  Select **Save Current Validation Run** to store a run in the local
    SQLite history.

## Understanding the checks

-   **Schema validation:** identifies columns missing from or extra in
    the target and data-type differences in shared columns.
-   **Missing-value analysis:** counts null/empty values recognized by
    Pandas in each column.
-   **Duplicate analysis:** reports duplicate rows in each dataset.
-   **Key reconciliation:** compares records only when the chosen key
    has no missing or duplicate values in either dataset.
-   **Numeric range rule:** flags non-missing target values lower than
    the configured minimum or greater than the configured maximum.
    Values exactly at either boundary pass.
-   **Data-quality score:** percentage of completed PASS/FAIL checks
    that passed. Checks marked `NOT RUN` are excluded from the
    calculation.

These checks are rule-based. A passing result does not prove that a
dataset is correct for every business use case, and numeric range checks
do not detect every type of anomaly.

## Testing checklist

Before presenting the project, verify:

-   [ ] The app starts without an error.
-   [ ] Both CSV and XLSX uploads work.
-   [ ] Missing-value and duplicate analyses display expected results.
-   [ ] Schema differences are reported correctly.
-   [ ] Reconciliation works with a unique, non-null shared key.
-   [ ] Values outside a configured numeric range are flagged.
-   [ ] CSV downloads open correctly.
-   [ ] The Excel workbook opens and contains the expected sheets.
-   [ ] Saving a validation run adds a row to history.
-   [ ] The history table and trend chart display after saving a run.

Use small test datasets with known issues so you can verify expected
outcomes.

## Limitations and future improvements

-   The numeric validation is a configurable range check, not a
    general-purpose anomaly detection model.
-   Reconciliation requires a suitable unique key and matching data
    representations across datasets.
-   Very large files may require streaming or chunked processing.
-   Validation rules are currently configured through the app rather
    than managed as reusable rule profiles.

Possible future improvements include downloadable PDF reports, reusable
validation-rule profiles, more data-type normalization options, and
automated test coverage.

## Academic project note

This application is intended as a learning and demonstration project.
Test it with synthetic, public, or otherwise authorized data, and
explain the checks and limitations clearly during the project
demonstration.
