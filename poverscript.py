import csv
import datetime
from pathlib import Path

# -----------------------------
# CONFIGURATION
# -----------------------------

INPUT_CSV = "members_input.csv"      # Source member list
OUTPUT_POVER = "pover_batch.txt"     # POVER file to submit to MARx

# Rollover mapping: original -> new
ROLLOVER_MAP = {
    # (old_contract, old_pbp): (new_contract, new_pbp)
    ("H1234", "042"): ("H1234", "045"),
    # add more mappings as needed
}

TRANSACTION_CODE = "61"              # POVER transaction code
ACTION_CODE = "A"                    # Add
ROLLOVER_INDICATOR = "Y"             # Rollover

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def normalize_date(date_str):
    """
    Accepts date in formats like YYYY-MM-DD or MM/DD/YYYY
    Returns CCYYMMDD or raises ValueError.
    """
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.strftime("%Y%m%d")
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date_str}")


def build_pover_record(
    mbi,
    dob,
    gender,
    eff_date,
    old_contract,
    old_pbp,
    new_contract,
    new_pbp,
):
    """
    Returns a single pipe-delimited POVER record line.
    Layout (example, adjust to your spec):

    0  Transaction Code (61)
    1  New Contract
    2  New PBP
    3  Effective Date
    4  MBI
    5  DOB
    6  Gender
    7  Action Code (A)
    8  Rollover Indicator (Y)
    9  Old Contract
    10 Old PBP
    """
    fields = [
        TRANSACTION_CODE,
        new_contract,
        new_pbp,
        eff_date,
        mbi,
        dob,
        gender,
        ACTION_CODE,
        ROLLOVER_INDICATOR,
        old_contract,
        old_pbp,
    ]
    return "|".join(fields)


# -----------------------------
# MAIN PROCESS
# -----------------------------

def create_pover_file(
    input_csv: str = INPUT_CSV,
    output_file: str = OUTPUT_POVER,
):
    input_path = Path(input_csv)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    total = 0
    written = 0
    rejects = []

    with input_path.open("r", newline="", encoding="utf-8-sig") as infile, \
         output_path.open("w", newline="", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)

        required_cols = [
            "MBI",
            "DOB",
            "Gender",
            "EffectiveDate",
            "Contract",
            "PBP",
        ]
        for col in required_cols:
            if col not in reader.fieldnames:
                raise ValueError(f"Missing required column in input CSV: {col}")

        for row in reader:
            total += 1
            try:
                mbi = row["MBI"].strip()
                dob = normalize_date(row["DOB"])
                gender = row["Gender"].strip().upper()
                eff_date = normalize_date(row["EffectiveDate"])
                old_contract = row["Contract"].strip().upper()
                old_pbp = row["PBP"].strip()

                key = (old_contract, old_pbp)
                if key not in ROLLOVER_MAP:
                    rejects.append((row, "No rollover mapping for contract/PBP"))
                    continue

                new_contract, new_pbp = ROLLOVER_MAP[key]

                line = build_pover_record(
                    mbi=mbi,
                    dob=dob,
                    gender=gender,
                    eff_date=eff_date,
                    old_contract=old_contract,
                    old_pbp=old_pbp,
                    new_contract=new_contract,
                    new_pbp=new_pbp,
                )
                outfile.write(line + "\n")
                written += 1

            except Exception as ex:
                rejects.append((row, str(ex)))
                continue

    print(f"POVER generation complete.")
    print(f"Total input records: {total}")
    print(f"POVER records written: {written}")
    print(f"Rejected records: {len(rejects)}")

    if rejects:
        reject_log = output_path.with_suffix(".rejects.csv")
        with reject_log.open("w", newline="", encoding="utf-8") as rejfile:
            fieldnames = ["Reason"] + (reader.fieldnames or [])
            writer = csv.DictWriter(rejfile, fieldnames=fieldnames)
            writer.writeheader()
            for row, reason in rejects:
                row_out = dict(row)
                row_out["Reason"] = reason
                writer.writerow(row_out)
        print(f"Rejects written to: {reject_log}")


if __name__ == "__main__":
    create_pover_file()
