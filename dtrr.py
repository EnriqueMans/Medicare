"""
dtrr_processor.py

Reads a fixed-width DTRR file from C:/app/input, filters to TC61 records,
and writes a fixed-width output file to C:/app/output using the same
DTRR column widths (missing columns auto-padded with spaces).

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

# ---------------------------------------------------------------------------
# DTRR Detail Record layout (Layout 3-23, PCUG v19.4) - 102 fields, 800 bytes
# ---------------------------------------------------------------------------

DTRR_WIDTHS = [
    12,12,7,1,1,8,1,5,2,3,1,1,1,1,3,2,1,8,1,3,1,8,1,12,3,8,2,6,5,3,
    8,2,1,3,8,8,1,1,1,1,3,1,1,15,8,3,7,1,1,1,20,15,1,3,1,8,8,8,8,8,
    6,10,15,20,6,10,8,1,8,1,1,1,15,2,1,10,1,1,3,3,8,8,8,13,2,2,2,1,
    8,1,1,19,20,15,7,10,1,8,12,10,74,169
]

DTRR_COLUMNS = [
    "Beneficiary_ID","Surname","First_Name","Middle_Initial","Sex_Code",
    "Date_of_Birth","Record_Type","Contract_Number","State_Code","County_Code",
    "Disability_Indicator","Hospice_Indicator","Institutional_NHC_HCBS_Indicator",
    "ESRD_Indicator","Transaction_Reply_Code","Transaction_Code","Entitlement_Type_Code",
    "Effective_Date","WA_Indicator","Plan_Benefit_Package_ID","Filler_21",
    "Transaction_Date","UI_Initiated_Change_Flag","TRC_Dependent_Data_24",
    "District_Office_Code","Prev_Part_D_Contract_PBP_TrOOP","SEP_Reason_Code",
    "Filler_28","Source_ID","Prior_Plan_Benefit_Package_ID","Application_Date",
    "UI_User_Org_Designation","Out_of_Area_Flag","Segment_Number",
    "Part_C_Beneficiary_Premium","Part_D_Beneficiary_Premium","Election_Type_Code",
    "Enrollment_Source_Code","Part_D_Opt_Out_Flag","Premium_Withhold_Option_C_D",
    "Cumulative_Number_Uncovered_Months","Creditable_Coverage_Flag",
    "Employer_Subsidy_Override_Flag","Processing_Timestamp","End_Date",
    "Submitted_Number_Uncovered_Months","Filler_47","Preferred_Language_Other_Than_English",
    "Accessible_Format","Secondary_Drug_Insurance_Flag","Secondary_Rx_ID",
    "Secondary_Rx_Group","EGHP","Part_D_Low_Income_Premium_Subsidy_Level",
    "Low_Income_Co_Pay_Category","Low_Income_Period_Effective_Date",
    "Part_D_Late_Enrollment_Penalty_Amount","Part_D_Late_Enrollment_Penalty_Waived_Amount",
    "Part_D_Late_Enrollment_Penalty_Subsidy_Amount","Low_Income_Part_D_Premium_Subsidy_Amount",
    "Part_D_Rx_BIN","Part_D_Rx_PCN","Part_D_Rx_Group","Part_D_Rx_ID","Secondary_Rx_BIN",
    "Secondary_Rx_PCN","De_Minimis_Differential_Amount","MSP_Status_Flag",
    "Low_Income_Period_End_Date","Low_Income_Subsidy_Source_Code",
    "Enrollee_Type_Flag_PBP_Level","Application_Date_Indicator","TRC_Short_Name",
    "Disenrollment_Reason_Code","MMP_Opt_Out_Flag","Cleanup_ID",
    "CARA_Status_Add_Update_Delete_Flag","POS_Drug_Edit_Status","Drug_Class",
    "POS_Drug_Edit_Code","CARA_Status_Notification_Start_Date",
    "CARA_Status_Implementation_Start_Date","CARA_Status_Notification_End_Date",
    "Hospice_Provider_Number","IC_Model_Type_Indicator","IC_Model_End_Date_Reason_Code",
    "IC_Model_Benefit_Status","Updated_Medicaid_Status_Community_RAF",
    "CARA_Status_Implementation_End_Date","Prescriber_Limitation","Pharmacy_Limitation",
    "Filler_92","System_Assigned_Transaction_Tracking_ID","Plan_Assigned_Transaction_Tracking_ID",
    "Relationship_to_Enrollee","National_Producer_Number","OEC_Indicator",
    "OEC_Application_Date","OEC_Application_Number","Beneficiary_Phone_Number",
    "Beneficiary_Email_Address","Filler_102"
]

assert len(DTRR_WIDTHS) == len(DTRR_COLUMNS) == 102
assert sum(DTRR_WIDTHS) == 800

# Fields CMS requires for TC 61 (per PCUG "Transactions Missing CMS Data" table)
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
# Core read / write functions
# ---------------------------------------------------------------------------

def read_fwf_strict(path, widths=DTRR_WIDTHS, columns=DTRR_COLUMNS, encoding="utf-8"):
    """Read a fixed-width DTRR file, asserting every line matches the expected length."""
    expected_len = sum(widths)
    colspecs = []
    pos = 0
    for w in widths:
        colspecs.append((pos, pos + w))
        pos += w

    with open(path, encoding=encoding, errors="replace") as f:
        for i, line in enumerate(f, start=1):
            line_len = len(line.rstrip("\n").rstrip("\r"))
            if line_len != expected_len:
                raise ValueError(
                    f"{path} line {i}: length {line_len} != expected {expected_len}"
                )

    df = pd.read_fwf(path, colspecs=colspecs, names=columns, dtype=str, encoding=encoding)
    return df


def write_fwf(df, path, widths=DTRR_WIDTHS, columns=DTRR_COLUMNS, warn_missing=True):
    """
    Vectorized fixed-width writer.
    - Columns in `columns` not present in df are auto-padded with spaces.
    - Extra columns in df not in `columns` are ignored.
    - Raises if any value exceeds its column's width.
    """
    width_by_col = dict(zip(columns, widths))
    total_width = sum(widths)

    missing_cols = [c for c in columns if c not in df.columns]
    if warn_missing and missing_cols:
        print(f"[write_fwf] Padding {len(missing_cols)} missing column(s) with spaces.")

    df2 = df.reindex(columns=columns)
    df2 = df2.fillna("").astype(str)
    df2 = df2.replace("nan", "")

    overflow = {}
    for col in columns:
        w = width_by_col[col]
        too_long = df2[col].str.len() > w
        if too_long.any():
            overflow[col] = df2.index[too_long].tolist()
    if overflow:
        raise ValueError(f"Values exceed column width: {overflow}")

    for col in columns:
        df2[col] = df2[col].str.ljust(width_by_col[col])

    lines = df2[columns[0]].str.cat(df2[columns[1:]], sep="")

    bad_len = lines.str.len() != total_width
    if bad_len.any():
        raise ValueError(f"Row(s) with wrong total length: {lines.index[bad_len].tolist()}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def split_scc(df, scc_column="SCC", state_col="State_Code", county_col="County_Code"):
    """If SCC arrives as a single 5-digit code, split into State_Code (2) + County_Code (3)."""
    if scc_column in df.columns:
        df[state_col] = df[scc_column].astype(str).str[:2]
        df[county_col] = df[scc_column].astype(str).str[2:5]
    return df


# ---------------------------------------------------------------------------
# Main pipeline: read input dir -> filter TC61 -> write output dir
# ---------------------------------------------------------------------------

def find_input_file(input_dir):
    """Find the file to process in the input directory (first non-directory file found)."""
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    candidates = [
        f for f in glob.glob(os.path.join(input_dir, "*"))
        if os.path.isfile(f)
    ]
    if not candidates:
        raise FileNotFoundError(f"No files found in input directory: {input_dir}")
    if len(candidates) > 1:
        print(f"[main] Multiple files found in {input_dir}, using the first: {candidates[0]}")
    return candidates[0]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    input_path = find_input_file(INPUT_DIR)
    input_filename = os.path.basename(input_path)
    output_path = os.path.join(OUTPUT_DIR, input_filename)

    print(f"[main] Reading: {input_path}")
    df = read_fwf_strict(input_path)
    print(f"[main] Read {len(df)} total records.")

    # Filter to TC61 records only
    df_tc61 = df[df["Transaction_Code"] == "61"].copy()
    print(f"[main] {len(df_tc61)} TC61 records found.")

    if df_tc61.empty:
        print("[main] No TC61 records to write. Exiting without creating output file.")
        return

    df_tc61 = split_scc(df_tc61)  # no-op if "SCC" column isn't present

    print(f"[main] Writing: {output_path}")
    write_fwf(df_tc61, output_path)
    print("[main] Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
