"""
dtrr_processor.py

Reads a fixed-width DTRR file from C:/app/input, filters to TC61 records,
validates CMS-required TC61 fields, and writes a fixed-width output file
to C:/app/output using the DTRR Layout 3-23 column widths.

CMS MAPD Plan Communications User Guide v19.4
DTRR Detail Record - Layout 3-23
Record length: 800 characters

Usage:
    python dtrr_processor.py
"""

import os
import sys
import glob
import pandas as pd


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

INPUT_DIR = r"C:/app/input"
OUTPUT_DIR = r"C:/app/output"

ENCODING = "utf-8"

# Transaction Code to retain
TC61_TRANSACTION_CODE = "61"


# ---------------------------------------------------------------------------
# DTRR Detail Record Layout
#
# CMS MAPD Plan Communications User Guide v19.4
# Layout 3-23 - DTRR Data File Detail Record
#
# 102 fields / 800 characters
# ---------------------------------------------------------------------------

DTRR_WIDTHS = [
    12, 12, 7, 1, 1, 8, 1, 5, 2, 3, 1, 1, 1, 1, 3, 2, 1, 8, 1, 3,
    1, 8, 1, 12, 3, 8, 2, 6, 5, 3, 8, 2, 1, 3, 8, 8, 1, 1, 1, 1,
    3, 1, 1, 15, 8, 3, 7, 1, 1, 1, 20, 15, 1, 3, 1, 8, 8, 8, 8, 8,
    6, 10, 15, 20, 6, 10, 8, 1, 8, 1, 1, 1, 15, 2, 1, 10, 1, 1, 3, 3,
    8, 8, 8, 13, 2, 2, 2, 1, 8, 1, 1, 19, 20, 15, 7, 10, 1, 8, 12,
    10, 74, 169
]


DTRR_COLUMNS = [
    "Beneficiary_ID",
    "Surname",
    "First_Name",
    "Middle_Initial",
    "Sex_Code",
    "Date_of_Birth",
    "Record_Type",
    "Contract_Number",
    "State_Code",
    "County_Code",
    "Disability_Indicator",
    "Hospice_Indicator",
    "Institutional_NHC_HCBS_Indicator",
    "ESRD_Indicator",
    "Transaction_Reply_Code",
    "Transaction_Code",
    "Entitlement_Type_Code",
    "Effective_Date",
    "WA_Indicator",
    "Plan_Benefit_Package_ID",
    "Filler_21",
    "Transaction_Date",
    "UI_Initiated_Change_Flag",
    "TRC_Dependent_Data_24",
    "District_Office_Code",
    "Prev_Part_D_Contract_PBP_TrOOP",
    "SEP_Reason_Code",
    "Filler_28",
    "Source_ID",
    "Prior_Plan_Benefit_Package_ID",
    "Application_Date",
    "UI_User_Org_Designation",
    "Out_of_Area_Flag",
    "Segment_Number",
    "Part_C_Beneficiary_Premium",
    "Part_D_Beneficiary_Premium",
    "Election_Type_Code",
    "Enrollment_Source_Code",
    "Part_D_Opt_Out_Flag",
    "Premium_Withhold_Option_C_D",
    "Cumulative_Number_Uncovered_Months",
    "Creditable_Coverage_Flag",
    "Employer_Subsidy_Override_Flag",
    "Processing_Timestamp",
    "End_Date",
    "Submitted_Number_Uncovered_Months",
    "Filler_47",
    "Preferred_Language_Other_Than_English",
    "Accessible_Format",
    "Secondary_Drug_Insurance_Flag",
    "Secondary_Rx_ID",
    "Secondary_Rx_Group",
    "EGHP",
    "Part_D_Low_Income_Premium_Subsidy_Level",
    "Low_Income_Co_Pay_Category",
    "Low_Income_Period_Effective_Date",
    "Part_D_Late_Enrollment_Penalty_Amount",
    "Part_D_Late_Enrollment_Penalty_Waived_Amount",
    "Part_D_Late_Enrollment_Penalty_Subsidy_Amount",
    "Low_Income_Part_D_Premium_Subsidy_Amount",
    "Part_D_Rx_BIN",
    "Part_D_Rx_PCN",
    "Part_D_Rx_Group",
    "Part_D_Rx_ID",
    "Secondary_Rx_BIN",
    "Secondary_Rx_PCN",
    "De_Minimis_Differential_Amount",
    "MSP_Status_Flag",
    "Low_Income_Period_End_Date",
    "Low_Income_Subsidy_Source_Code",
    "Enrollee_Type_Flag_PBP_Level",
    "Application_Date_Indicator",
    "TRC_Short_Name",
    "Disenrollment_Reason_Code",
    "MMP_Opt_Out_Flag",
    "Cleanup_ID",
    "CARA_Status_Add_Update_Delete_Flag",
    "POS_Drug_Edit_Status",
    "Drug_Class",
    "POS_Drug_Edit_Code",
    "CARA_Status_Notification_Start_Date",
    "CARA_Status_Implementation_Start_Date",
    "CARA_Status_Notification_End_Date",
    "Hospice_Provider_Number",
    "IC_Model_Type_Indicator",
    "IC_Model_End_Date_Reason_Code",
    "IC_Model_Benefit_Status",
    "Updated_Medicaid_Status_Community_RAF",
    "CARA_Status_Implementation_End_Date",
    "Prescriber_Limitation",
    "Pharmacy_Limitation",
    "Filler_92",
    "System_Assigned_Transaction_Tracking_ID",
    "Plan_Assigned_Transaction_Tracking_ID",
    "Relationship_to_Enrollee",
    "National_Producer_Number",
    "OEC_Indicator",
    "OEC_Application_Date",
    "OEC_Application_Number",
    "Beneficiary_Phone_Number",
    "Beneficiary_Email_Address",
    "Filler_102",
]


# ---------------------------------------------------------------------------
# CMS-required fields for Transaction Code 61
#
# These fields are validated for TC61 records.
# ---------------------------------------------------------------------------

TC61_REQUIRED_COLUMNS = [
    "Application_Date",
    "Date_of_Birth",
    "Contract_Number",
    "Effective_Date",
    "Election_Type_Code",
    "First_Name",
    "Beneficiary_ID",
    "Part_C_Beneficiary_Premium",
    "Plan_Benefit_Package_ID",
    "Premium_Withhold_Option_C_D",
    "Segment_Number",
    "Sex_Code",
    "Surname",
    "Transaction_Code",
    "State_Code",
    "County_Code",
]


# ---------------------------------------------------------------------------
# Layout validation
# ---------------------------------------------------------------------------

EXPECTED_FIELD_COUNT = 102
EXPECTED_RECORD_LENGTH = 800


def validate_layout():
    """Validate the DTRR layout configuration."""

    if len(DTRR_WIDTHS) != EXPECTED_FIELD_COUNT:
        raise ValueError(
            f"DTRR_WIDTHS contains {len(DTRR_WIDTHS)} fields; "
            f"expected {EXPECTED_FIELD_COUNT}."
        )

    if len(DTRR_COLUMNS) != EXPECTED_FIELD_COUNT:
        raise ValueError(
            f"DTRR_COLUMNS contains {len(DTRR_COLUMNS)} fields; "
            f"expected {EXPECTED_FIELD_COUNT}."
        )

    if len(DTRR_WIDTHS) != len(DTRR_COLUMNS):
        raise ValueError(
            "DTRR_WIDTHS and DTRR_COLUMNS must contain the same number of fields."
        )

    actual_length = sum(DTRR_WIDTHS)

    if actual_length != EXPECTED_RECORD_LENGTH:
        raise ValueError(
            f"DTRR layout totals {actual_length} characters; "
            f"expected {EXPECTED_RECORD_LENGTH}."
        )

    missing_required_columns = [
        column
        for column in TC61_REQUIRED_COLUMNS
        if column not in DTRR_COLUMNS
    ]

    if missing_required_columns:
        raise ValueError(
            "TC61 required columns missing from DTRR layout: "
            + ", ".join(missing_required_columns)
        )


# ---------------------------------------------------------------------------
# Fixed-width parser
# ---------------------------------------------------------------------------

def read_fwf_strict(
    path,
    widths=DTRR_WIDTHS,
    columns=DTRR_COLUMNS,
    encoding=ENCODING,
):
    """
    Read a fixed-width DTRR file using exact character positions.

    Every physical record must contain exactly 800 characters,
    excluding CR/LF line terminators.

    Values are NOT stripped while parsing because spaces are significant
    in a fixed-width CMS file.
    """

    expected_len = sum(widths)

    records = []

    with open(path, "r", encoding=encoding, errors="replace", newline="") as f:

        for line_number, line in enumerate(f, start=1):

            # Remove only line terminators.
            line = line.rstrip("\r\n")

            actual_len = len(line)

            if actual_len != expected_len:
                raise ValueError(
                    f"{path} line {line_number}: "
                    f"length {actual_len} != expected {expected_len}"
                )

            record = {}

            position = 0

            for column, width in zip(columns, widths):

                record[column] = line[position:position + width]

                position += width

            records.append(record)

    return pd.DataFrame(records, columns=columns)


# ---------------------------------------------------------------------------
# TC61 filtering
# ---------------------------------------------------------------------------

def filter_tc61(df):
    """
    Return only Transaction Code 61 records.

    Values are stripped for comparison, but the original fixed-width
    values remain unchanged in the resulting dataframe.
    """

    if "Transaction_Code" not in df.columns:
        raise ValueError(
            "Transaction_Code column is missing from the DTRR layout."
        )

    transaction_codes = (
        df["Transaction_Code"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    return df[transaction_codes == TC61_TRANSACTION_CODE].copy()


# ---------------------------------------------------------------------------
# TC61 required-field validation
# ---------------------------------------------------------------------------

def validate_tc61_required_fields(df):
    """
    Validate CMS-required fields for TC61 records.

    A required field is considered missing when, after stripping
    surrounding spaces, it contains no value.

    Raises ValueError if any required values are missing.
    """

    if df.empty:
        return

    problems = {}

    for column in TC61_REQUIRED_COLUMNS:

        if column not in df.columns:
            problems[column] = "column missing"
            continue

        missing_mask = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
        )

        if missing_mask.any():

            row_indexes = df.index[missing_mask].tolist()

            problems[column] = row_indexes

    if problems:

        formatted_problems = []

        for column, rows in problems.items():

            if rows == "column missing":
                formatted_problems.append(
                    f"{column}: column missing"
                )
            else:
                formatted_problems.append(
                    f"{column}: missing on dataframe row(s) {rows}"
                )

        raise ValueError(
            "TC61 record validation failed. "
            "Required CMS data is missing:\n  - "
            + "\n  - ".join(formatted_problems)
        )


# ---------------------------------------------------------------------------
# Fixed-width writer
# ---------------------------------------------------------------------------

def write_fwf(
    df,
    path,
    widths=DTRR_WIDTHS,
    columns=DTRR_COLUMNS,
    encoding=ENCODING,
    warn_missing=True,
):
    """
    Write a dataframe as an exact fixed-width DTRR file.

    Behavior:
      - Columns not present in df are automatically padded with spaces.
      - Extra dataframe columns are ignored.
      - Values are left-aligned within their CMS-defined widths.
      - Values exceeding their widths cause an error.
      - Every output record must be exactly 800 characters.
    """

    width_by_col = dict(zip(columns, widths))
    total_width = sum(widths)

    # Identify missing columns.
    missing_columns = [
        column
        for column in columns
        if column not in df.columns
    ]

    if warn_missing and missing_columns:
        print(
            f"[write_fwf] Padding "
            f"{len(missing_columns)} missing column(s) with spaces:"
        )

        for column in missing_columns:
            print(f"    - {column}")

    # Reindex guarantees CMS column order.
    df2 = df.reindex(columns=columns).copy()

    # Replace missing values with empty strings.
    df2 = df2.fillna("")

    # Convert everything to strings.
    df2 = df2.astype(str)

    # Protect against string representation of NaN.
    df2 = df2.replace("nan", "")

    # -----------------------------------------------------------------------
    # Check for values exceeding field widths.
    # -----------------------------------------------------------------------

    overflow = {}

    for column in columns:

        width = width_by_col[column]

        too_long = df2[column].str.len() > width

        if too_long.any():

            overflow[column] = {
                "width": width,
                "rows": df2.index[too_long].tolist(),
                "values": df2.loc[too_long, column].tolist(),
            }

    if overflow:

        messages = []

        for column, details in overflow.items():

            messages.append(
                f"{column} "
                f"(width={details['width']}, "
                f"rows={details['rows']}, "
                f"values={details['values']})"
            )

        raise ValueError(
            "One or more values exceed their CMS field widths:\n  - "
            + "\n  - ".join(messages)
        )

    # -----------------------------------------------------------------------
    # Pad every field to its defined width.
    # -----------------------------------------------------------------------

    for column in columns:

        width = width_by_col[column]

        df2[column] = df2[column].str.ljust(width)

    # -----------------------------------------------------------------------
    # Concatenate fields into 800-character records.
    # -----------------------------------------------------------------------

    if df2.empty:
        lines = pd.Series(dtype=str)
    else:

        lines = df2[columns[0]].copy()

        for column in columns[1:]:
            lines = lines + df2[column]

    # -----------------------------------------------------------------------
    # Verify every record is exactly 800 characters.
    # -----------------------------------------------------------------------

    if not lines.empty:

        bad_length = lines.str.len() != total_width

        if bad_length.any():

            bad_rows = lines.index[bad_length].tolist()

            raise ValueError(
                "Output row(s) have incorrect total length: "
                f"{bad_rows}"
            )

    # -----------------------------------------------------------------------
    # Create output directory if necessary.
    # -----------------------------------------------------------------------

    os.makedirs(os.path.dirname(path), exist_ok=True)

    # -----------------------------------------------------------------------
    # Write records.
    # -----------------------------------------------------------------------

    with open(path, "w", encoding=encoding, newline="") as f:

        if not lines.empty:

            f.write("\n".join(lines.tolist()))

            # Final newline is standard for text files.
            f.write("\n")

    print(
        f"[write_fwf] Wrote {len(lines)} record(s), "
        f"{total_width} characters per record."
    )


# ---------------------------------------------------------------------------
# Optional SCC handling
# ---------------------------------------------------------------------------

def split_scc(
    df,
    scc_column="SCC",
    state_col="State_Code",
    county_col="County_Code",
):
    """
    If an upstream dataframe contains an SCC column containing
    a 5-character State+County code, split it into State_Code
    and County_Code.

    This is normally a no-op for a native DTRR Layout 3-23 file because
    State_Code and County_Code are already separate fields.
    """

    if scc_column not in df.columns:
        return df

    scc = (
        df[scc_column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Validate SCC length when populated.
    invalid = (
        (scc != "")
        & (scc.str.len() != 5)
    )

    if invalid.any():

        rows = df.index[invalid].tolist()

        raise ValueError(
            f"SCC must contain exactly 5 characters. "
            f"Invalid row(s): {rows}"
        )

    df[state_col] = scc.str[:2]
    df[county_col] = scc.str[2:5]

    return df


# ---------------------------------------------------------------------------
# Input file discovery
# ---------------------------------------------------------------------------

def find_input_file(input_dir):
    """
    Find the input file.

    If multiple files exist, the first file returned by the filesystem
    is used and a warning is printed.
    """

    if not os.path.isdir(input_dir):

        raise FileNotFoundError(
            f"Input directory not found: {input_dir}"
        )

    candidates = [
        path
        for path in glob.glob(os.path.join(input_dir, "*"))
        if os.path.isfile(path)
    ]

    if not candidates:

        raise FileNotFoundError(
            f"No files found in input directory: {input_dir}"
        )

    # Sort for deterministic behavior.
    candidates.sort()

    if len(candidates) > 1:

        print(
            f"[main] Multiple files found in {input_dir}. "
            f"Using: {candidates[0]}"
        )

        print("[main] Other files:")

        for path in candidates[1:]:
            print(f"    - {path}")

    return candidates[0]


# ---------------------------------------------------------------------------
# Main processing pipeline
# ---------------------------------------------------------------------------

def main():

    print("=" * 70)
    print("DTRR TC61 Processor")
    print("CMS MAPD Plan Communications User Guide v19.4")
    print("DTRR Layout 3-23")
    print("=" * 70)

    # -----------------------------------------------------------------------
    # Validate the hard-coded layout before touching any files.
    # -----------------------------------------------------------------------

    print("[main] Validating DTRR layout...")
    validate_layout()

    print(
        f"[main] Layout validated: "
        f"{len(DTRR_COLUMNS)} fields / "
        f"{sum(DTRR_WIDTHS)} characters."
    )

    # -----------------------------------------------------------------------
    # Ensure output directory exists.
    # -----------------------------------------------------------------------

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # -----------------------------------------------------------------------
    # Find input.
    # -----------------------------------------------------------------------

    input_path = find_input_file(INPUT_DIR)

    input_filename = os.path.basename(input_path)

    output_path = os.path.join(
        OUTPUT_DIR,
        input_filename,
    )

    print(f"[main] Input : {input_path}")
    print(f"[main] Output: {output_path}")

    # -----------------------------------------------------------------------
    # Read input.
    # -----------------------------------------------------------------------

    print("[main] Reading DTRR...")

    df = read_fwf_strict(
        input_path,
        widths=DTRR_WIDTHS,
        columns=DTRR_COLUMNS,
        encoding=ENCODING,
    )

    print(
        f"[main] Read {len(df):,} total record(s)."
    )

    # -----------------------------------------------------------------------
    # Filter TC61.
    # -----------------------------------------------------------------------

    df_tc61 = filter_tc61(df)

    print(
        f"[main] Found {len(df_tc61):,} TC61 record(s)."
    )

    # -----------------------------------------------------------------------
    # Nothing to write.
    # -----------------------------------------------------------------------

    if df_tc61.empty:

        print(
            "[main] No TC61 records found. "
            "No output file will be created."
        )

        return

    # -----------------------------------------------------------------------
    # Validate required CMS fields.
    # -----------------------------------------------------------------------

    print("[main] Validating required TC61 fields...")

    validate_tc61_required_fields(df_tc61)

    print(
        "[main] Required TC61 fields validated successfully."
    )

    # -----------------------------------------------------------------------
    # Optional SCC processing.
    #
    # Native DTRR records already contain State_Code and County_Code,
    # so this normally does nothing.
    # -----------------------------------------------------------------------

    df_tc61 = split_scc(df_tc61)

    # -----------------------------------------------------------------------
    # Write output.
    # -----------------------------------------------------------------------

    print("[main] Writing TC61 output...")

    write_fwf(
        df_tc61,
        output_path,
        widths=DTRR_WIDTHS,
        columns=DTRR_COLUMNS,
        encoding=ENCODING,
        warn_missing=True,
    )

    # -----------------------------------------------------------------------
    # Final verification.
    # -----------------------------------------------------------------------

    print("[main] Verifying output file...")

    if not os.path.isfile(output_path):

        raise FileNotFoundError(
            f"Output file was not created: {output_path}"
        )

    output_size = os.path.getsize(output_path)

    print(
        f"[main] Output file size: {output_size:,} bytes"
    )

    # Read output again and verify every record is 800 characters.
    with open(
        output_path,
        "r",
        encoding=ENCODING,
        errors="replace",
        newline="",
    ) as f:

        output_lines = f.readlines()

    for line_number, line in enumerate(output_lines, start=1):

        line = line.rstrip("\r\n")

        if len(line) != EXPECTED_RECORD_LENGTH:

            raise ValueError(
                f"Output verification failed: "
                f"line {line_number} has {len(line)} characters; "
                f"expected {EXPECTED_RECORD_LENGTH}."
            )

    if len(output_lines) != len(df_tc61):

        raise ValueError(
            f"Output verification failed: "
            f"expected {len(df_tc61)} records, "
            f"found {len(output_lines)}."
        )

    print(
        f"[main] Output verified: "
        f"{len(output_lines):,} record(s), "
        f"{EXPECTED_RECORD_LENGTH} characters each."
    )

    print("[main] Done.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    try:
        main()

    except Exception as exc:

        print(
            f"[ERROR] {exc}",
            file=sys.stderr,
        )

        sys.exit(1)
