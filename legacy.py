"""
Create a TriZetto EAM "Request File" (fixed-width, 312 chars/row) from a DataFrame.

Expected DataFrame columns:
    MBI, MemberID, PlanID, PBPID, TransactionCode, EffectiveDate,
    UpdateType, FileDate, FacetsErrorMessages (optional)

Notes / assumptions (confirm with TriZetto):
    - Text fields are left-justified and space-padded.
    - PBPID and TransactionCode are zero-padded (e.g. 1 -> "001", 5 -> "05").
    - UpdateType 1 (Member file): TransactionCode and EffectiveDate are blank.
    - Dates may be datetime objects or strings; output is MMDDYYYY.
    - Over-length values raise an error instead of being silently truncated
      (except FacetsErrorMessages, which is optional and is truncated).
"""
import pandas as pd

FIELDS = [
    ("MBI", 15),
    ("MemberID", 15),
    ("PlanID", 5),
    ("PBPID", 3),
    ("TransactionCode", 2),
    ("EffectiveDate", 8),
    ("UpdateType", 1),
    ("FileDate", 8),
    ("FacetsErrorMessages", 255),
]
RECORD_LENGTH = sum(width for _, width in FIELDS)  # 312


def _text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _date(value):
    s = _text(value)
    if not s:
        return ""
    if len(s) == 8 and s.isdigit():  # already MMDDYYYY
        return pd.to_datetime(s, format="%m%d%Y").strftime("%m%d%Y")
    return pd.to_datetime(value).strftime("%m%d%Y")


def _int_text(value, width):
    s = _text(value)
    if not s:
        return ""
    return str(int(float(s))).zfill(width)


def build_record(row):
    update_type = _int_text(row["UpdateType"], 1)
    if update_type not in ("1", "2"):
        raise ValueError(f"UpdateType must be 1 or 2, got {update_type!r}")

    if update_type == "2":
        txn_code = _int_text(row["TransactionCode"], 2)
        eff_date = _date(row["EffectiveDate"])
        if not txn_code or not eff_date:
            raise ValueError("UpdateType 2 requires TransactionCode and EffectiveDate")
    else:
        txn_code, eff_date = "", ""

    errors = _text(row.get("FacetsErrorMessages", ""))
    errors = " ".join(errors.split())  # strip newlines/tabs
    errors = errors.encode("ascii", "replace").decode("ascii")[:255]

    values = {
        "MBI": _text(row["MBI"]),
        "MemberID": _text(row["MemberID"]),
        "PlanID": _text(row["PlanID"]),
        "PBPID": _int_text(row["PBPID"], 3),
        "TransactionCode": txn_code,
        "EffectiveDate": eff_date,
        "UpdateType": update_type,
        "FileDate": _date(row["FileDate"]),
        "FacetsErrorMessages": errors,
    }

    parts = []
    for name, width in FIELDS:
        v = values[name]
        if len(v) > width:
            raise ValueError(f"{name} is {len(v)} chars; max is {width}: {v!r}")
        parts.append(v.ljust(width))
    line = "".join(parts)
    assert len(line) == RECORD_LENGTH
    return line


def write_request_file(df, path, newline="\r\n"):
    """Write df to a fixed-width EAM request file. Returns number of rows written."""
    df = df.copy()
    if "FacetsErrorMessages" not in df.columns:
        df["FacetsErrorMessages"] = ""

    required = [n for n, _ in FIELDS if n != "FacetsErrorMessages"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    lines, problems = [], []
    for idx, row in df.iterrows():
        try:
            lines.append(build_record(row))
        except Exception as e:
            problems.append(f"row {idx}: {e}")

    if problems:
        raise ValueError("Cannot write file:\n" + "\n".join(problems))

    with open(path, "w", encoding="ascii", newline="") as f:
        for line in lines:
            f.write(line + newline)
    return len(lines)


if __name__ == "__main__":
    # Example. Read CSVs with dtype=str to preserve leading zeros.
    sample = pd.DataFrame(
        [
            {
                "MBI": "1EG4TE5MK73", "MemberID": "M000123", "PlanID": "H1234",
                "PBPID": "001", "TransactionCode": "61", "EffectiveDate": "2026-01-01",
                "UpdateType": 2, "FileDate": "2026-11-15",
                "FacetsErrorMessages": "Invalid subscriber ID,Duplicate span",
            },
            {
                "MBI": "1EG4TE5MK73", "MemberID": "M000123", "PlanID": "H1234",
                "PBPID": "001", "TransactionCode": None, "EffectiveDate": None,
                "UpdateType": 1, "FileDate": "2026-11-15", "FacetsErrorMessages": "",
            },
        ]
    )
    n = write_request_file(sample, "eam_request_file.txt")
    print(f"Wrote {n} records")
