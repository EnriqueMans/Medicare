"""
extract_tc61.py

Reads a MARx Batch Input Transaction Data File (fixed-width, one record per
line) and extracts only the TC 61 (Enrollment) detail records.

Outputs:
  1. A raw copy of the file containing only TC 61 lines (same fixed-width
     format as the input -- unparsed, byte-for-byte).
  2. A parsed CSV of the TC 61 records, split into named columns per the
     EAM_COLUMN_MAP layout (positions 1-600).

Usage:
    python extract_tc61.py input_file.txt
    python extract_tc61.py input_file.txt --raw-out tc61_only.txt --csv-out tc61_parsed.csv

Notes:
  - Transaction Code is at file positions 60-61 (1-indexed). This script
    checks that slice for the literal value "61".
  - Positions are 1-indexed per the CMS layout; Python slicing is
    converted accordingly (start-1 : end).
  - Blank/short lines and lines shorter than the record length are skipped
    with a warning printed to stderr.
"""

import argparse
import csv
import sys

RECORD_LENGTH = 600

# (field_name, start_pos, end_pos) -- 1-indexed, inclusive, per CMS Layout 3-9
TC61_FIELDS = [
    ("beneficiary_id",            1,   12),
    ("surname",                   13,  24),
    ("first_name",                25,  31),
    ("middle_initial",            32,  32),
    ("sex_code",                  33,  33),
    ("birth_date",                34,  41),
    ("eghp_flag",                 42,  42),
    ("pbp_num",                   43,  45),
    ("election_type_code",        46,  46),
    ("contract_id",               47,  51),
    ("application_date",          52,  59),
    ("transaction_code",          60,  61),
    # filler                      62,  63
    ("effective_date",            64,  71),
    ("segment_id",                72,  74),
    # filler                      75,  79
    ("esrd_override",             80,  80),
    ("ppo_parts_cd",              81,  81),
    ("part_c_premium",            82,  87),
    # filler                      88,  93
    ("creditable_coverage_flag",  94,  94),
    ("nuncmo",                    95,  97),
    ("employer_subsidy_flag",     98,  98),
    ("part_d_opt_out_flag",       99,  99),
    # filler                      100, 100
    ("sep_reason_code",           101, 102),
    # filler                      103, 123
    ("preferred_language",        124, 124),
    ("accessible_format",         125, 125),
    # filler                      126, 134
    ("secondary_drug_ins_flag",   135, 135),
    ("secondary_rx_id",           136, 155),
    ("secondary_rx_group",        156, 170),
    ("enrollment_source_code",    171, 171),
    ("rolled_from_contract",      172, 176),
    ("rolled_from_pbp",           177, 179),
    # filler                      180, 209
    ("transaction_tracking_id",   210, 224),
    ("part_d_rx_bin",             225, 230),
    ("part_d_rx_pcn",             231, 240),
    ("part_d_rx_group",           241, 255),
    ("part_d_rx_id",              256, 275),
    ("secondary_drug_bin",        276, 281),
    ("secondary_drug_pcn",        282, 291),
    ("rel_agent",                 292, 292),
    ("rel_broker",                293, 293),
    ("rel_ship",                  294, 294),
    ("rel_auth_rep",              295, 295),
    ("rel_other",                 296, 296),
    ("rel_self",                  297, 297),
    ("rel_form_blank",            298, 298),
    ("npn",                       299, 308),
    ("oec_indicator",             309, 309),
    ("oec_app_date",              310, 317),
    ("oec_app_number",            318, 329),
    ("bene_phone",                330, 339),
    ("bene_email",                340, 413),
    # filler                      414, 600
]

TC_START, TC_END = 60, 61  # 1-indexed positions of the Transaction Code


def is_tc61(line: str) -> bool:
    """Return True if the fixed-width line's Transaction Code == '61'."""
    if len(line) < TC_END:
        return False
    return line[TC_START - 1:TC_END] == "61"


def parse_record(line: str) -> dict:
    """Split a fixed-width TC 61 line into a dict of named, stripped fields."""
    row = {}
    for name, start, end in TC61_FIELDS:
        row[name] = line[start - 1:end].strip() if len(line) >= start else ""
    return row


def process(input_path: str, raw_out_path: str, csv_out_path: str) -> int:
    tc61_lines = []
    total_lines = 0
    skipped_short = 0

    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line:
                continue
            total_lines += 1
            if len(line) < RECORD_LENGTH:
                skipped_short += 1
            if is_tc61(line):
                tc61_lines.append(line)

    # 1. Raw filtered copy (unparsed, same fixed-width format)
    with open(raw_out_path, "w", encoding="utf-8") as f:
        for line in tc61_lines:
            f.write(line + "\n")

    # 2. Parsed CSV
    fieldnames = [name for name, _, _ in TC61_FIELDS]
    with open(csv_out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for line in tc61_lines:
            writer.writerow(parse_record(line))

    print(f"Total lines read:        {total_lines}", file=sys.stderr)
    print(f"Lines shorter than {RECORD_LENGTH} chars: {skipped_short}", file=sys.stderr)
    print(f"TC 61 records found:     {len(tc61_lines)}", file=sys.stderr)
    print(f"Raw TC 61 copy written:  {raw_out_path}", file=sys.stderr)
    print(f"Parsed CSV written:      {csv_out_path}", file=sys.stderr)

    return len(tc61_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract TC 61 (Enrollment) records from a MARx batch file."
    )
    parser.add_argument("input_file", help="Path to the MARx batch input file")
    parser.add_argument(
        "--raw-out",
        default="tc61_only.txt",
        help="Output path for the raw filtered fixed-width file (default: tc61_only.txt)",
    )
    parser.add_argument(
        "--csv-out",
        default="tc61_parsed.csv",
        help="Output path for the parsed CSV (default: tc61_parsed.csv)",
    )
    args = parser.parse_args()

    process(args.input_file, args.raw_out, args.csv_out)


if __name__ == "__main__":
    main()
