import io
import sqlite3
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="DataGuard | Data Quality",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ DataGuard")
st.subheader("Data Quality Monitoring & Anomaly Detection")
st.write(
    "Upload source and target datasets to compare their structure, "
    "validate records, and identify data quality issues."
)
st.caption("Use synthetic, public, or otherwise authorized datasets only.")


# --------------------------------------------------
# 2. DATA UPLOAD AND INPUT VALIDATION
# --------------------------------------------------
st.header("📂 Upload Datasets")
col1, col2 = st.columns(2)

with col1:
    source_file = st.file_uploader(
        "Upload Source Dataset", type=["csv", "xlsx"], key="source_upload"
    )
with col2:
    target_file = st.file_uploader(
        "Upload Target Dataset", type=["csv", "xlsx"], key="target_upload"
    )


def load_dataset(uploaded_file):
    """Load and validate a CSV or XLSX upload."""
    if uploaded_file is None:
        return None

    try:
        uploaded_file.seek(0)
        file_name = uploaded_file.name.lower()
        if file_name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif file_name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            st.error(f"Unsupported file format: {uploaded_file.name}")
            return None

        if df.empty:
            st.error(f"{uploaded_file.name} contains no data.")
            return None
        if len(df.columns) == 0:
            st.error(f"{uploaded_file.name} has no columns.")
            return None

        # Normalize column names before checking duplicates.
        df.columns = df.columns.map(str).str.strip()
        if df.columns.duplicated().any():
            duplicate_names = df.columns[df.columns.duplicated()].tolist()
            st.error(
                f"{uploaded_file.name} has duplicate column names after trimming "
                f"spaces: {duplicate_names}. Rename them and upload again."
            )
            return None
        return df
    except pd.errors.EmptyDataError:
        st.error(f"{uploaded_file.name} is empty or has no readable data.")
    except pd.errors.ParserError:
        st.error(f"{uploaded_file.name} is not a valid CSV file.")
    except Exception as error:
        st.error(f"Could not read {uploaded_file.name}: {error}")
    return None


if source_file is None or target_file is None:
    st.info("Upload both datasets to begin validation.")
    st.stop()

source_df = load_dataset(source_file)
target_df = load_dataset(target_file)
if source_df is None or target_df is None:
    st.stop()
st.success("Both datasets loaded successfully.")


# --------------------------------------------------
# 3. DATASET OVERVIEW
# --------------------------------------------------
st.divider()
st.header("📊 Dataset Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Source Records", len(source_df))
col2.metric("Target Records", len(target_df))
col3.metric("Record Count Difference", len(target_df) - len(source_df))
col4.metric("Target Missing Values", int(target_df.isna().sum().sum()))
col5, col6 = st.columns(2)
col5.metric("Source Missing Values", int(source_df.isna().sum().sum()))
col6.metric("Target Duplicate Rows", int(target_df.duplicated().sum()))


# --------------------------------------------------
# 4. DATASET COMPARISON
# --------------------------------------------------
st.divider()
st.header("📋 Dataset Comparison")
source_metrics = {
    "Total records": len(source_df),
    "Total columns": len(source_df.columns),
    "Missing values": int(source_df.isna().sum().sum()),
    "Duplicate complete rows": int(source_df.duplicated().sum()),
}
target_metrics = {
    "Total records": len(target_df),
    "Total columns": len(target_df.columns),
    "Missing values": int(target_df.isna().sum().sum()),
    "Duplicate complete rows": int(target_df.duplicated().sum()),
}
comparison = pd.DataFrame({
    "Metric": list(source_metrics.keys()),
    "Source": list(source_metrics.values()),
    "Target": list(target_metrics.values()),
})
comparison["Difference (Target - Source)"] = comparison["Target"] - comparison["Source"]
st.dataframe(comparison, use_container_width=True, hide_index=True)


# --------------------------------------------------
# 5. SCHEMA VALIDATION
# --------------------------------------------------
st.divider()
st.header("🔍 Schema Validation")
source_columns = set(source_df.columns)
target_columns = set(target_df.columns)
missing_columns = sorted(source_columns - target_columns)
extra_columns = sorted(target_columns - source_columns)
common_columns = [column for column in source_df.columns if column in target_df.columns]

col1, col2 = st.columns(2)
with col1:
    st.subheader("Missing in Target")
    if missing_columns:
        st.error(f"{len(missing_columns)} missing column(s)")
        st.write(missing_columns)
    else:
        st.success("No source columns are missing.")
with col2:
    st.subheader("Extra in Target")
    if extra_columns:
        st.warning(f"{len(extra_columns)} extra column(s)")
        st.write(extra_columns)
    else:
        st.success("No extra target columns.")
st.metric("Common Columns", len(common_columns))

type_mismatches = []
for column in common_columns:
    source_type = str(source_df[column].dtype)
    target_type = str(target_df[column].dtype)
    if source_type != target_type:
        type_mismatches.append({
            "Column": column,
            "Source Type": source_type,
            "Target Type": target_type,
        })
if type_mismatches:
    st.warning(f"{len(type_mismatches)} data type mismatch(es) detected.")
    st.dataframe(pd.DataFrame(type_mismatches), use_container_width=True, hide_index=True)
else:
    st.success("Data types match for all shared columns.")
schema_pass = not missing_columns and not extra_columns and not type_mismatches
if schema_pass:
    st.success("Schema validation passed.")
else:
    st.error("Schema validation failed.")


# --------------------------------------------------
# 6. MISSING VALUE ANALYSIS
# --------------------------------------------------
st.divider()
st.header("🕳️ Missing Value Analysis")
st.write("Review missing values by column in the source and target datasets.")
source_missing = source_df.isna().sum()
target_missing = target_df.isna().sum()
missing_analysis = pd.DataFrame({
    "Column": sorted(set(source_df.columns) | set(target_df.columns))
})
missing_analysis["Source Missing"] = missing_analysis["Column"].map(source_missing).fillna(0).astype(int)
missing_analysis["Target Missing"] = missing_analysis["Column"].map(target_missing).fillna(0).astype(int)
missing_analysis["Source Missing %"] = missing_analysis.apply(
    lambda row: round(row["Source Missing"] / len(source_df) * 100, 2)
    if row["Column"] in source_df.columns else 0.0, axis=1
)
missing_analysis["Target Missing %"] = missing_analysis.apply(
    lambda row: round(row["Target Missing"] / len(target_df) * 100, 2)
    if row["Column"] in target_df.columns else 0.0, axis=1
)
col1, col2 = st.columns(2)
col1.metric("Source Missing Cells", int(source_missing.sum()))
col2.metric("Target Missing Cells", int(target_missing.sum()))
nonzero_missing = missing_analysis[
    (missing_analysis["Source Missing"] > 0) | (missing_analysis["Target Missing"] > 0)
]
if nonzero_missing.empty:
    st.success("No missing values found in either dataset.")
else:
    st.dataframe(nonzero_missing, use_container_width=True, hide_index=True)
    chart_data = nonzero_missing.melt(
        id_vars="Column",
        value_vars=["Source Missing", "Target Missing"],
        var_name="Dataset",
        value_name="Missing Values",
    )
    st.bar_chart(chart_data, x="Column", y="Missing Values", color="Dataset")


# --------------------------------------------------
# 7. DUPLICATE RECORD ANALYSIS
# --------------------------------------------------
st.divider()
st.header("🔁 Duplicate Record Analysis")
col1, col2 = st.columns(2)
source_duplicates = source_df[source_df.duplicated(keep=False)]
target_duplicates = target_df[target_df.duplicated(keep=False)]
with col1:
    st.subheader("Source Duplicates")
    st.metric("Rows involved in duplicates", len(source_duplicates))
    if not source_duplicates.empty:
        st.dataframe(source_duplicates, use_container_width=True, hide_index=True)
    else:
        st.success("No duplicate complete rows in source.")
with col2:
    st.subheader("Target Duplicates")
    st.metric("Rows involved in duplicates", len(target_duplicates))
    if not target_duplicates.empty:
        st.dataframe(target_duplicates, use_container_width=True, hide_index=True)
    else:
        st.success("No duplicate complete rows in target.")


# --------------------------------------------------
# 8. KEY-BASED RECORD RECONCILIATION
# --------------------------------------------------
st.divider()
st.header("🔗 Source vs Target Reconciliation")
st.write(
    "Choose a shared column that uniquely identifies each record, "
    "such as an order ID, employee ID, or transaction ID."
)
source_only = pd.DataFrame(columns=source_df.columns)
target_only = pd.DataFrame(columns=target_df.columns)
mismatch_details = []
reconciliation_status = "NOT RUN"
reconciliation_details = "Reconciliation was not run."

if not common_columns:
    st.warning("The datasets have no shared columns. Reconciliation cannot be performed.")
else:
    key_column = st.selectbox("Select record key", options=common_columns, key="reconciliation_key")
    source_key_missing = int(source_df[key_column].isna().sum())
    target_key_missing = int(target_df[key_column].isna().sum())
    source_key_duplicates = int(source_df[key_column].dropna().duplicated().sum())
    target_key_duplicates = int(target_df[key_column].dropna().duplicated().sum())
    if source_key_missing or target_key_missing:
        st.warning(f"Missing key values — Source: {source_key_missing}, Target: {target_key_missing}.")
    if source_key_duplicates or target_key_duplicates:
        st.warning(
            f"Duplicate key values — Source: {source_key_duplicates}, Target: {target_key_duplicates}. "
            "Reconciliation requires a unique, non-missing key."
        )
    if not (source_key_missing or target_key_missing or source_key_duplicates or target_key_duplicates):
        source_keys = set(source_df[key_column])
        target_keys = set(target_df[key_column])
        source_only_keys = source_keys - target_keys
        target_only_keys = target_keys - source_keys
        source_only = source_df[source_df[key_column].isin(source_only_keys)]
        target_only = target_df[target_df[key_column].isin(target_only_keys)]
        col1, col2 = st.columns(2)
        col1.metric("Records Missing in Target", len(source_only))
        col2.metric("Extra Records in Target", len(target_only))
        if not source_only.empty:
            with st.expander("View records missing from Target"):
                st.dataframe(source_only, use_container_width=True, hide_index=True)
        if not target_only.empty:
            with st.expander("View extra records in Target"):
                st.dataframe(target_only, use_container_width=True, hide_index=True)

        source_indexed = source_df.set_index(key_column)
        target_indexed = target_df.set_index(key_column)
        shared_keys = sorted(source_keys & target_keys, key=str)
        for column in common_columns:
            if column == key_column:
                continue
            source_values = source_indexed.loc[shared_keys, column]
            target_values = target_indexed.loc[shared_keys, column]
            equal_values = source_values.eq(target_values) | (source_values.isna() & target_values.isna())
            for key_value in equal_values.index[~equal_values]:
                mismatch_details.append({
                    "Key": key_value,
                    "Column": column,
                    "Source Value": source_indexed.loc[key_value, column],
                    "Target Value": target_indexed.loc[key_value, column],
                })
        st.subheader("Field-Level Mismatches")
        if mismatch_details:
            st.warning(f"Found {len(mismatch_details)} field mismatch(es).")
            st.dataframe(pd.DataFrame(mismatch_details), use_container_width=True, hide_index=True)
        else:
            st.success("All shared records match across common non-key columns.")
        reconciliation_status = "FAIL" if (not source_only.empty or not target_only.empty or mismatch_details) else "PASS"
        reconciliation_details = (
            f"Missing in target: {len(source_only)}; extra in target: {len(target_only)}; "
            f"field mismatches: {len(mismatch_details)}."
        )
    else:
        reconciliation_details = (
            f"Cannot compare because key issues were found. Missing key values — "
            f"source: {source_key_missing}, target: {target_key_missing}; duplicate key values — "
            f"source: {source_key_duplicates}, target: {target_key_duplicates}."
        )


# --------------------------------------------------
# 9. CONFIGURABLE NUMERIC VALIDATION RULES
# --------------------------------------------------
st.divider()
st.header("📏 Configurable Numeric Validation Rules")
rule_check_status = "NOT RUN"
rule_check_details = "No numeric rule has been evaluated."
invalid_rows = pd.DataFrame()
selected_numeric_column = None
min_value = None
max_value = None
numeric_columns = target_df.select_dtypes(include="number").columns.tolist()

if numeric_columns:
    selected_numeric_column = st.selectbox(
        "Select numeric column", numeric_columns, key="rule_numeric_column"
    )
    values = target_df[selected_numeric_column].dropna()
    if values.empty:
        st.info("The selected column has no numeric values.")
        rule_check_details = "No numeric values available for validation."
    else:
        col1, col2 = st.columns(2)
        with col1:
            min_value = st.number_input(
                "Minimum allowed value", value=float(values.min()), key="rule_min_value"
            )
        with col2:
            max_value = st.number_input(
                "Maximum allowed value", value=float(values.max()), key="rule_max_value"
            )
        if min_value > max_value:
            st.error("Minimum value cannot be greater than maximum value.")
            rule_check_details = "Invalid rule configuration: minimum exceeds maximum."
        else:
            invalid_rows = target_df[
                target_df[selected_numeric_column].notna()
                & ((target_df[selected_numeric_column] < min_value)
                   | (target_df[selected_numeric_column] > max_value))
            ]
            total_checked = len(values)
            failed_count = len(invalid_rows)
            if failed_count:
                st.warning(
                    f"{failed_count} of {total_checked} non-missing value(s) are outside "
                    f"the allowed range {min_value} to {max_value}."
                )
                st.dataframe(invalid_rows, use_container_width=True, hide_index=True)
                rule_check_status = "FAIL"
            else:
                st.success(f"All {total_checked} non-missing values pass the numeric rule.")
                rule_check_status = "PASS"
            rule_check_details = (
                f"Column: {selected_numeric_column}; checked: {total_checked}; "
                f"failed: {failed_count}; allowed range: {min_value} to {max_value}."
            )
else:
    st.info("No numeric columns are available in the target dataset.")
    rule_check_details = "No numeric columns available for validation."


# --------------------------------------------------
# 10. DATA EXPLORER
# --------------------------------------------------
st.divider()
st.header("🧭 Data Explorer")
dataset_choice = st.radio("Select dataset to preview", ["Source", "Target"], horizontal=True)
selected_df = source_df if dataset_choice == "Source" else target_df
st.caption(f"Total records: {len(selected_df)}")
preview_rows = st.selectbox(
    "Rows to preview", [10, 25, 50, 100], index=1, key="data_explorer_preview_rows"
)
st.dataframe(selected_df.head(preview_rows), use_container_width=True, hide_index=True)
st.download_button(
    label="Download complete dataset as CSV",
    data=selected_df.to_csv(index=False).encode("utf-8"),
    file_name=f"{dataset_choice.lower()}_dataset.csv",
    mime="text/csv",
)


# --------------------------------------------------
# 11. VALIDATION REPORT
# --------------------------------------------------
st.divider()
st.header("📄 Validation Report")
report_rows = [
    {"Check": "Source file loaded", "Status": "PASS", "Details": f"{len(source_df)} records loaded"},
    {"Check": "Target file loaded", "Status": "PASS", "Details": f"{len(target_df)} records loaded"},
    {
        "Check": "Record count match",
        "Status": "PASS" if len(source_df) == len(target_df) else "FAIL",
        "Details": f"Source: {len(source_df)}, Target: {len(target_df)}",
    },
    {
        "Check": "Schema match",
        "Status": "PASS" if schema_pass else "FAIL",
        "Details": f"Missing columns: {missing_columns}; Extra columns: {extra_columns}; Type mismatches: {type_mismatches}",
    },
    {
        "Check": "Target missing values",
        "Status": "PASS" if int(target_df.isna().sum().sum()) == 0 else "FAIL",
        "Details": f"{int(target_df.isna().sum().sum())} missing value(s)",
    },
    {
        "Check": "Target duplicate rows",
        "Status": "PASS" if target_df.duplicated().sum() == 0 else "FAIL",
        "Details": f"{int(target_df.duplicated().sum())} duplicate complete row(s)",
    },
    {"Check": "Key-based reconciliation", "Status": reconciliation_status, "Details": reconciliation_details},
    {"Check": "Configurable numeric rule", "Status": rule_check_status, "Details": rule_check_details},
]
report_df = pd.DataFrame(report_rows)
passed_checks = int((report_df["Status"] == "PASS").sum())
failed_checks = int((report_df["Status"] == "FAIL").sum())
not_run_checks = int((report_df["Status"] == "NOT RUN").sum())
total_checks = len(report_df)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Checks", total_checks)
col2.metric("Passed", passed_checks)
col3.metric("Failed", failed_checks)
col4.metric("Not Run", not_run_checks)
st.dataframe(report_df, use_container_width=True, hide_index=True)
st.download_button(
    "⬇️ Download Validation Report",
    data=report_df.to_csv(index=False).encode("utf-8"),
    file_name="dataguard_validation_report.csv",
    mime="text/csv",
)


# --------------------------------------------------
# 12. VALIDATION SUMMARY AND QUALITY SCORE
# --------------------------------------------------
st.divider()
st.header("📈 Validation Summary")
chart_data = pd.DataFrame({
    "Status": ["PASS", "FAIL", "NOT RUN"],
    "Count": [passed_checks, failed_checks, not_run_checks],
})
st.bar_chart(chart_data, x="Status", y="Count")
completed_checks = passed_checks + failed_checks
if completed_checks > 0:
    quality_score = (passed_checks / completed_checks) * 100
    col1, col2 = st.columns([1, 2])
    col1.metric("Data Quality Score", f"{quality_score:.1f}%")
    col2.progress(quality_score / 100)
    st.caption(
        f"Based on {completed_checks} completed checks "
        f"({passed_checks} passed, {failed_checks} failed). NOT RUN checks are excluded."
    )
    if failed_checks:
        st.warning("Some validation checks failed. Review the report above.")
    elif not_run_checks:
        st.info("All completed checks passed, but some checks were not run.")
    else:
        st.success("All validation checks passed.")
else:
    quality_score = 0.0
    st.info("No completed validation checks are available to calculate a score.")


# --------------------------------------------------
# 13. DOWNLOAD FAILED NUMERIC RECORDS
# --------------------------------------------------
st.divider()
st.header("⬇️ Download Failed Numeric Records")
if not invalid_rows.empty and selected_numeric_column is not None:
    failed_export = invalid_rows.copy()
    failed_export["Validation Rule"] = selected_numeric_column
    failed_export["Minimum Allowed"] = min_value
    failed_export["Maximum Allowed"] = max_value
    st.write(f"{len(failed_export)} record(s) failed the numeric validation rule.")
    st.dataframe(failed_export, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Failed Records",
        data=failed_export.to_csv(index=False).encode("utf-8"),
        file_name="dataguard_failed_records.csv",
        mime="text/csv",
    )
else:
    st.success("No failed records are available for download under the current numeric rule.")


# --------------------------------------------------
# 14. SCHEMA COMPARISON REPORT
# --------------------------------------------------
st.divider()
st.header("🧾 Schema Comparison Report")
schema_report = []
for column in sorted(source_columns | target_columns):
    if column not in target_columns:
        status, source_type, target_type = "Missing in Target", str(source_df[column].dtype), "-"
    elif column not in source_columns:
        status, source_type, target_type = "Extra in Target", "-", str(target_df[column].dtype)
    elif source_df[column].dtype != target_df[column].dtype:
        status, source_type, target_type = "Data Type Mismatch", str(source_df[column].dtype), str(target_df[column].dtype)
    else:
        status, source_type, target_type = "Match", str(source_df[column].dtype), str(target_df[column].dtype)
    schema_report.append({
        "Column": column,
        "Source Data Type": source_type,
        "Target Data Type": target_type,
        "Status": status,
    })
schema_report_df = pd.DataFrame(schema_report)
st.dataframe(schema_report_df, use_container_width=True, hide_index=True)
st.download_button(
    "Download Schema Comparison Report",
    data=schema_report_df.to_csv(index=False).encode("utf-8"),
    file_name="dataguard_schema_report.csv",
    mime="text/csv",
)


# --------------------------------------------------
# 15. EXPORT COMPLETE EXCEL REPORT
# --------------------------------------------------
st.divider()
st.header("📦 Export Complete Validation Report")
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    report_df.to_excel(writer, index=False, sheet_name="Validation Summary")
    schema_report_df.to_excel(writer, index=False, sheet_name="Schema Comparison")
    missing_analysis.to_excel(writer, index=False, sheet_name="Missing Values")
    comparison.to_excel(writer, index=False, sheet_name="Dataset Comparison")
    if mismatch_details:
        pd.DataFrame(mismatch_details).to_excel(writer, index=False, sheet_name="Field Mismatches")
    if not invalid_rows.empty:
        invalid_rows.to_excel(writer, index=False, sheet_name="Numeric Failures")
st.download_button(
    "Download Complete Excel Report",
    data=excel_buffer.getvalue(),
    file_name="dataguard_validation_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)


# --------------------------------------------------
# 16. VALIDATION HISTORY (SQLITE)
# --------------------------------------------------
st.divider()
st.header("🗃️ Validation History")
database_path = "dataguard_history.db"
with sqlite3.connect(database_path) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS validation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_time TEXT,
            total_checks INTEGER,
            passed_checks INTEGER,
            failed_checks INTEGER,
            not_run_checks INTEGER,
            quality_score REAL
        )
    """)
if st.button("Save Current Validation Run"):
    current_score = (passed_checks / completed_checks * 100) if completed_checks else 0.0
    with sqlite3.connect(database_path) as conn:
        conn.execute("""
            INSERT INTO validation_history (
                run_time, total_checks, passed_checks, failed_checks,
                not_run_checks, quality_score
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_checks, passed_checks, failed_checks, not_run_checks, current_score,
        ))
    st.success("Validation run saved successfully.")

with sqlite3.connect(database_path) as conn:
    history_df = pd.read_sql_query(
        "SELECT * FROM validation_history ORDER BY id DESC", conn
    )
if not history_df.empty:
    st.dataframe(history_df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Validation History",
        data=history_df.to_csv(index=False).encode("utf-8"),
        file_name="dataguard_validation_history.csv",
        mime="text/csv",
    )
    trend_df = history_df.copy()
    trend_df["run_time"] = pd.to_datetime(trend_df["run_time"], errors="coerce")
    trend_df = trend_df.dropna(subset=["run_time"]).sort_values("id")
    if not trend_df.empty:
        st.subheader("Validation History Trend")
        st.line_chart(trend_df, x="run_time", y="quality_score")
        st.caption("Data quality score for each saved validation run.")
else:
    st.info("No validation history saved yet. Save a run to start tracking trends.")


# --------------------------------------------------
# 17. ABOUT DATAGUARD
# --------------------------------------------------
st.divider()
st.header("About DataGuard")
st.markdown("""
**DataGuard** is a Data Quality Monitoring and Anomaly Detection System developed as a B.Tech CSE mini project.

### Key Features
- Source and target dataset comparison
- Schema and data type validation
- Missing value and duplicate record analysis
- Configurable numeric range validation
- Key-based source-to-target reconciliation
- Downloadable CSV and Excel validation reports
- SQLite validation history and data quality score tracking

### Technology Stack
- **Python** — Core programming language
- **Streamlit** — Interactive web application
- **Pandas** — Data processing and analysis
- **Plotly** — Visualization
- **SQLite** — Validation history storage
- **OpenPyXL** — Excel report generation

### Project Objective
Help users identify data quality issues, compare datasets, review validation results, and export reports through a single interface.

**Important:** Numeric range validation checks only the rule configured by the user; it does not automatically detect every possible anomaly.
""")
