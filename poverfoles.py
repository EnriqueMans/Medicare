import csv
import datetime
from pathlib import Path

# ---------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------

INPUT_CSV = "members_input.csv"
OUTPUT_FILE = "pover_fixedwidth.txt"

ROLLOVER_MAP = {
    ("H1234", "042"): ("H1234", "045"),
}

TRANSACTION_CODE = "61"
ACTION_CODE = "A"
ROLLOVER_INDICATOR = "Y"

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def normalize_date(date_str):
    """Convert various date formats to CCYYMMDD."""
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.strftime("%Y%m%d")
        except ValueError:
            pass
    raise ValueError(f"Invalid date format: {date_str}")


def fw(value, length):
    """Fixed-width field: left-justified, padded with spaces."""
    return str(value).ljust(length)[:length]


def build_pover_record(
    mbi, dob, gender, eff_date,
    old_contract, old_pbp,
    new_contract, new_pbp
):
    """
    Build a 48-character fixed-width POVER record.
    """
    return (
        fw(TRANSACTION_CODE, 2) +
        fw(new_contract, 5) +
        fw(new_pbp, 3) +
        fw(eff_date, 8) +
        fw(mbi, 11) +
        fw(dob, 8) +
        fw(gender, 1) +
        fw(ACTION_CODE, 1) +
        fw(ROLLOVER_INDICATOR, 1) +
        fw(old_contract, 5) +
        fw(old_pbp, 3)
    )


# ---------------------------------------------------
# MAIN PROCESS
# ---------------------------------------------------

def create_pover_fixedwidth(input_csv=INPUT_CSV, output_file=OUTPUT_FILE):
    input_path = Path(input_csv)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    rejects = []
    written = 0

    with input_path.open("r", newline="", encoding="utf-8-sig") as infile, \
         output_path.open("w", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)

        for row in reader:
            try:
                mbi = row["MBI"].strip()
                dob = normalize_date(row["DOB"])
                gender = row["Gender"].strip().upper()
                eff_date = normalize_date(row["EffectiveDate"])
                old_contract = row["Contract"].strip().upper()
                old_pbp = row["PBP"].strip()

                key = (old_contract, old_pbp)
                if key not in ROLLOVER_MAP:
                    rejects.append((row, "No rollover mapping"))
                    continue

                new_contract, new_pbp = ROLLOVER_MAP[key]

                line = build_pover_record(
                    mbi, dob, gender, eff_date,
                    old_contract, old_pbp,
                    new_contract, new_pbp
                )

                outfile.write(line + "\n")
                written += 1

            except Exception as ex:
                rejects.append((row, str(ex)))

    print(f"POVER fixed-width file created: {output_file}")
    print(f"Records written: {written}")
    print(f"Rejected: {len(rejects)}")


if __name__ == "__main__":
    create_pover_fixedwidth()
