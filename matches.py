"""
Script: match_eaf_trr.py

Purpose:
  1. Read a tab-separated .eaf.txt file.
  2. Keep only rows that contain the string "mbi" (in any column, or a
     specific column if you set MATCH_COLUMN below).
  3. Compare those rows against a second tab-separated "trr" file, matching
     on the first 12 characters of a chosen column.
  4. Write matching rows to an output text file.

>>> EDIT THE SETTINGS BELOW TO MATCH YOUR REAL FILES <<<
"""

import csv
import os

# ---------------------- SETTINGS (edit these) ----------------------

INPUT_FOLDER = r"c:/temp/input"          # folder containing the .eaf.txt file
EAF_FILENAME_SUFFIX = ".eaf.txt"         # will find the first file ending in this

TRR_FILE = r"c:/temp/temp_trr.txt"       # the "trr" file to match against
OUTPUT_FILE = r"c:/temp/matched_output.txt"

SEPARATOR = "\t"                         # tab-separated

SEARCH_TERM = "mbi"                      # string to search for in eaf rows
# Set to a column index (0-based) to restrict the "mbi" search to one column,
# or leave as None to search all columns in each row.
MBI_COLUMN = None

# Column index (0-based) used for the first-12-characters match in EACH file.
# Set these to the correct column number for your data.
EAF_MATCH_COLUMN = 0
TRR_MATCH_COLUMN = 0

MATCH_LENGTH = 12                        # number of characters to compare

# ---------------------------------------------------------------------


def find_eaf_file(folder, suffix):
    for fname in os.listdir(folder):
        if fname.lower().endswith(suffix.lower()):
            return os.path.join(folder, fname)
    raise FileNotFoundError(f"No file ending in '{suffix}' found in {folder}")


def load_rows(filepath, sep):
    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=sep)
        return [row for row in reader if row]  # skip empty rows


def row_contains_term(row, term, column=None):
    if column is not None:
        if column < len(row):
            return term.lower() in row[column].lower()
        return False
    return any(term.lower() in cell.lower() for cell in row)


def get_match_key(row, column, length):
    if column < len(row):
        return row[column].strip()[:length].lower()
    return ""


def main():
    eaf_path = find_eaf_file(INPUT_FOLDER, EAF_FILENAME_SUFFIX)
    print(f"Using eaf file: {eaf_path}")

    eaf_rows = load_rows(eaf_path, SEPARATOR)
    trr_rows = load_rows(TRR_FILE, SEPARATOR)

    # Filter eaf rows containing "mbi"
    mbi_rows = [r for r in eaf_rows if row_contains_term(r, SEARCH_TERM, MBI_COLUMN)]
    print(f"Rows containing '{SEARCH_TERM}': {len(mbi_rows)}")

    # Build a set of match keys from the trr file (first 12 chars of chosen column)
    trr_keys = {get_match_key(r, TRR_MATCH_COLUMN, MATCH_LENGTH) for r in trr_rows}

    # Find eaf rows (from the mbi-filtered set) whose match key appears in trr_keys
    matched_rows = [
        r for r in mbi_rows
        if get_match_key(r, EAF_MATCH_COLUMN, MATCH_LENGTH) in trr_keys
    ]
    print(f"Rows matching trr file on first {MATCH_LENGTH} chars: {len(matched_rows)}")

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=SEPARATOR)
        for row in matched_rows:
            writer.writerow(row)

    print(f"Done. Output written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
