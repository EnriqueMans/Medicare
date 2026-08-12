"""
Script: match_eaf_trr.py

Purpose:
  1. Read the .eaf.txt file (tab-separated, WITH a header row that includes
     a column named "MBI").
  2. Read the trr file (fixed-width, NO header, NO delimiter) where the
     first 12 characters of each line are the MBI value.
  3. Match eaf rows to trr lines where eaf's MBI value == trr's first
     12 characters.
  4. Write the matching rows into TWO SEPARATE output files:
       - matched eaf rows  -> MATCHED_EAF_OUTPUT
       - matched trr lines -> MATCHED_TRR_OUTPUT

>>> EDIT THE SETTINGS BELOW TO MATCH YOUR REAL FILES <<<
"""

import csv
import os

# ---------------------- SETTINGS (edit these) ----------------------

INPUT_FOLDER = r"c:/temp/input"          # folder containing the .eaf.txt file
EAF_FILENAME_SUFFIX = ".eaf.txt"         # will find the first file ending in this

TRR_FILE = r"c:/temp/temp_trr.txt"       # fixed-width trr file, no header

MATCHED_EAF_OUTPUT = r"c:/temp/matched_eaf.txt"   # matched rows FROM the eaf file
MATCHED_TRR_OUTPUT = r"c:/temp/matched_trr.txt"   # matched lines FROM the trr file

EAF_SEPARATOR = "\t"      # eaf file is tab-separated
MBI_COLUMN_NAME = "MBI"   # header name of the MBI column in the eaf file

MBI_WIDTH = 12            # trr file: MBI = first 12 characters of each line

# ---------------------------------------------------------------------


def find_eaf_file(folder, suffix):
    for fname in os.listdir(folder):
        if fname.lower().endswith(suffix.lower()):
            return os.path.join(folder, fname)
    raise FileNotFoundError(f"No file ending in '{suffix}' found in {folder}")


def load_eaf(filepath, sep, mbi_col_name):
    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=sep)
        rows = [row for row in reader if row]

    header = rows[0]
    data_rows = rows[1:]

    if mbi_col_name not in header:
        raise ValueError(
            f"Column '{mbi_col_name}' not found in eaf header: {header}"
        )
    mbi_idx = header.index(mbi_col_name)

    return header, data_rows, mbi_idx


def load_trr(filepath, width):
    """Return list of (raw_line, mbi_key) for each non-empty line."""
    lines = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        for line in f:
            raw = line.rstrip("\n").rstrip("\r")
            if raw.strip() == "":
                continue
            mbi_key = raw[:width].strip().lower()
            lines.append((raw, mbi_key))
    return lines


def main():
    eaf_path = find_eaf_file(INPUT_FOLDER, EAF_FILENAME_SUFFIX)
    print(f"Using eaf file: {eaf_path}")

    header, eaf_rows, mbi_idx = load_eaf(eaf_path, EAF_SEPARATOR, MBI_COLUMN_NAME)
    print(f"Eaf rows loaded: {len(eaf_rows)} (MBI is column index {mbi_idx})")

    trr_lines = load_trr(TRR_FILE, MBI_WIDTH)
    print(f"Trr lines loaded: {len(trr_lines)}")

    # Build lookup: mbi_key -> list of raw trr lines with that key
    trr_lookup = {}
    for raw, key in trr_lines:
        trr_lookup.setdefault(key, []).append(raw)

    matched_eaf_rows = []
    matched_trr_lines = []
    seen_trr_lines = set()

    for row in eaf_rows:
        if mbi_idx >= len(row):
            continue
        eaf_key = row[mbi_idx].strip().lower()
        if eaf_key in trr_lookup:
            matched_eaf_rows.append(row)
            for raw in trr_lookup[eaf_key]:
                if raw not in seen_trr_lines:
                    matched_trr_lines.append(raw)
                    seen_trr_lines.add(raw)

    print(f"Matched eaf rows: {len(matched_eaf_rows)}")
    print(f"Matched trr lines: {len(matched_trr_lines)}")

    # Write matched eaf rows (with header) to its own file
    with open(MATCHED_EAF_OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=EAF_SEPARATOR)
        writer.writerow(header)
        writer.writerows(matched_eaf_rows)

    # Write matched trr lines (raw, fixed-width) to its own file
    with open(MATCHED_TRR_OUTPUT, "w", encoding="utf-8", newline="") as f:
        for raw in matched_trr_lines:
            f.write(raw + "\n")

    print(f"Done.")
    print(f"  Matched eaf rows written to: {MATCHED_EAF_OUTPUT}")
    print(f"  Matched trr lines written to: {MATCHED_TRR_OUTPUT}")


if __name__ == "__main__":
    main()
