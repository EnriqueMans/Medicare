"""
Generate a pandas DataFrame of fake beneficiaries, then assign each row
into fixed-width BEQ Request / Response records per the MAPD PCUG v19.4
Chapter 3 layout (Layouts 3-1 through 3-6).

Usage:
    python3 generate_beq_from_dataframe.py

Outputs (same folder):
    BEQ_Request_Sample.txt   (750-byte records)
    BEQ_Response_Sample.txt  (2000-byte records)
    beq_beneficiaries.csv    (the source DataFrame, for reference)
"""

import random
import string
import pandas as pd

random.seed(42)  # remove or change for different fake data each run

# ============================================================
# Fixed-width helpers
# ============================================================

def blank(n):
    return [' '] * n

def set_field(buf, start, end, value, pad_char=' ', justify='left'):
    """1-indexed inclusive byte positions, per the layout spec."""
    width = end - start + 1
    value = '' if value is None else str(value)
    if justify == 'left':
        value = value.ljust(width, pad_char)[:width]
    else:
        value = value.rjust(width, pad_char)[:width]
    buf[start - 1:end] = list(value)

def record_to_str(buf):
    return ''.join(buf)

SENDING_ENTITY_REQ = "H1234"
SENDING_ENTITY_REQ_FIELD = SENDING_ENTITY_REQ.ljust(8)
FILE_CREATION_DATE = "20260809"
FILE_CONTROL_NUMBER = "000000001"

# ============================================================
# 1. Fake DataFrame of beneficiaries
# ============================================================

FIRST_NAMES = ["JOHN", "MARY", "ROBERT", "PATRICIA", "JAMES", "LINDA",
               "MICHAEL", "BARBARA", "WILLIAM", "ELIZABETH"]
LAST_NAMES = ["SMITH", "JOHNSON", "DAVIS", "MILLER", "WILSON",
              "MOORE", "TAYLOR", "ANDERSON", "THOMAS", "JACKSON"]
STATES = [("MD", "003", "BALTIMORE"), ("VA", "059", "ARLINGTON"),
          ("PA", "101", "PHILADELPHIA"), ("NY", "061", "NEW YORK"),
          ("OH", "035", "COLUMBUS")]
MBI_ALPHA = [c for c in string.ascii_uppercase if c not in "SLOIBZ"]  # CMS excludes these
MBI_ALPHANUM = MBI_ALPHA + [str(d) for d in range(10)]

def fake_mbi():
    """Loosely follows the CMS MBI character-position pattern (11 chars)."""
    pos = [
        random.choice(string.digits[1:]),       # 1: numeric 1-9
        random.choice(MBI_ALPHA),                # 2: alpha
        random.choice(MBI_ALPHANUM),              # 3: alphanumeric
        random.choice(string.digits),            # 4: numeric
        random.choice(MBI_ALPHA),                # 5: alpha
        random.choice(MBI_ALPHA),                # 6: alpha
        random.choice(string.digits),            # 7: numeric
        random.choice(string.digits),            # 8: numeric
        random.choice(MBI_ALPHA),                # 9: alpha
        random.choice(MBI_ALPHA),                # 10: alpha
        random.choice(string.digits),            # 11: numeric
    ]
    return ''.join(pos)

def fake_dob():
    year = random.randint(1935, 1959)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}{month:02d}{day:02d}"

def make_fake_dataframe(n=5, pct_matched=0.8):
    rows = []
    for i in range(n):
        matched = random.random() < pct_matched
        state, county, city = random.choice(STATES)
        rows.append(dict(
            seq=f"{i+1:07d}",
            beneficiary_id=fake_mbi(),
            dob=fake_dob(),
            sex=random.choice(["1", "2"]),
            matched=matched,
            first_name=random.choice(FIRST_NAMES),
            last_name=random.choice(LAST_NAMES),
            middle_initial=random.choice(string.ascii_uppercase),
            state_code=state,
            county_code=county,
            city=city,
            partA_start=f"{random.randint(1995,2020)}0101",
            partB_start=f"{random.randint(1995,2020)}0101",
            medicaid_ind=random.choice(["0", "0", "0", "1"]),  # mostly 0
            contract_number=f"H{random.randint(1000,9999)}",
            contract_start=f"{random.randint(2018,2025)}0101",
            pbp=f"{random.randint(1,20):03d}",
            plan_type=random.choice(["01", "02", "29", "31"]),
            eghp_ind="N",
            enroll_source="B",
            mailing_line1=f"{random.randint(100,999)} {random.choice(['MAIN','OAK','ELM','PARK'])} ST",
            mailing_zip=f"{random.randint(10000,99999)}0000",
            lis_copay_level=random.choice(["", "1", "2", "3"]),
            lis_premium_pct=random.choice(["", "100", "075", "050", "025"]),
        ))
    return pd.DataFrame(rows)

df = make_fake_dataframe(n=5, pct_matched=0.8)
df.to_csv("/home/claude/beq/mock/beq_beneficiaries.csv", index=False)
print(df)

# ============================================================
# 2. Request file builders (Layouts 3-1, 3-2, 3-3)
# ============================================================

def build_request_header():
    buf = blank(750)
    set_field(buf, 1, 8, "MMABEQRH")
    set_field(buf, 9, 16, SENDING_ENTITY_REQ_FIELD)
    set_field(buf, 17, 24, FILE_CREATION_DATE)
    set_field(buf, 25, 33, FILE_CONTROL_NUMBER)
    return record_to_str(buf)

def build_request_detail(row):
    buf = blank(750)
    set_field(buf, 1, 5, "DTL01")
    set_field(buf, 6, 17, row["beneficiary_id"])   # 12-char slot, 11-char MBI + space
    set_field(buf, 27, 34, row["dob"])
    set_field(buf, 35, 35, row["sex"])
    set_field(buf, 36, 42, row["seq"], pad_char='0', justify='right')
    return record_to_str(buf)

def build_request_trailer(record_count):
    buf = blank(750)
    set_field(buf, 1, 8, "MMABEQRT")
    set_field(buf, 9, 16, SENDING_ENTITY_REQ_FIELD)
    set_field(buf, 17, 24, FILE_CREATION_DATE)
    set_field(buf, 25, 33, FILE_CONTROL_NUMBER)
    set_field(buf, 34, 40, str(record_count), pad_char='0', justify='right')
    return record_to_str(buf)

# ============================================================
# 3. Response file builders (Layouts 3-4, 3-5, 3-6)
# ============================================================

def build_response_header():
    buf = blank(2000)
    set_field(buf, 1, 8, "CMSBEQRH")
    set_field(buf, 9, 16, "MBD".ljust(8))
    set_field(buf, 17, 24, FILE_CREATION_DATE)
    set_field(buf, 25, 33, FILE_CONTROL_NUMBER)
    return record_to_str(buf)

def build_response_trailer(record_count):
    buf = blank(2000)
    set_field(buf, 1, 8, "CMSBEQRT")
    set_field(buf, 9, 16, "MBD".ljust(8))
    set_field(buf, 17, 24, FILE_CREATION_DATE)
    set_field(buf, 25, 33, FILE_CONTROL_NUMBER)
    set_field(buf, 34, 40, str(record_count), pad_char='0', justify='right')
    return record_to_str(buf)

def build_response_detail(row):
    buf = blank(2000)
    # Echoed original detail record (Fields 1-7)
    set_field(buf, 1, 3, "DTL")
    set_field(buf, 4, 8, "01")
    set_field(buf, 9, 20, row["beneficiary_id"])
    set_field(buf, 30, 37, row["dob"])
    set_field(buf, 38, 38, row["sex"])
    set_field(buf, 39, 45, row["seq"], pad_char='0', justify='right')

    matched = bool(row["matched"])
    set_field(buf, 46, 46, "Y" if matched else "N")
    set_field(buf, 47, 47, "Y" if matched else "N")

    if matched:
        set_field(buf, 48, 55, row["partA_start"])
        set_field(buf, 64, 71, row["partB_start"])
        set_field(buf, 80, 80, row["medicaid_ind"])

        set_field(buf, 241, 248, SENDING_ENTITY_REQ_FIELD)
        set_field(buf, 249, 257, FILE_CONTROL_NUMBER)
        set_field(buf, 258, 265, FILE_CREATION_DATE)

        if row["lis_copay_level"]:
            set_field(buf, 274, 281, "20260101")
            set_field(buf, 282, 289, "20261231")
            set_field(buf, 290, 290, row["lis_copay_level"])
            set_field(buf, 291, 293, row["lis_premium_pct"])

        set_field(buf, 624, 631, row["dob"])
        set_field(buf, 632, 632, row["sex"])
        set_field(buf, 633, 672, row["last_name"])
        set_field(buf, 673, 702, row["first_name"])
        set_field(buf, 703, 703, row["middle_initial"])
        set_field(buf, 704, 705, row["state_code"])
        set_field(buf, 706, 708, row["county_code"])

        set_field(buf, 717, 721, row["contract_number"])
        set_field(buf, 722, 729, row["contract_start"])
        set_field(buf, 730, 730, "Y")
        set_field(buf, 746, 748, row["pbp"])
        set_field(buf, 749, 750, row["plan_type"])
        set_field(buf, 751, 751, row["eghp_ind"])
        set_field(buf, 1496, 1496, row["enroll_source"])

        set_field(buf, 758, 797, row["mailing_line1"])
        set_field(buf, 998, 1037, row["city"])
        set_field(buf, 1038, 1039, row["state_code"])
        set_field(buf, 1040, 1048, row["mailing_zip"])
        set_field(buf, 1049, 1056, row["contract_start"])

        set_field(buf, 1556, 1566, row["beneficiary_id"].strip())

    return record_to_str(buf)

# ============================================================
# 4. Assign each DataFrame row into the layouts and write files
# ============================================================

req_lines = [build_request_header()]
for _, row in df.iterrows():
    req_lines.append(build_request_detail(row))
req_lines.append(build_request_trailer(len(df)))

resp_lines = [build_response_header()]
for _, row in df.iterrows():
    resp_lines.append(build_response_detail(row))
resp_lines.append(build_response_trailer(len(df)))

for i, line in enumerate(req_lines):
    assert len(line) == 750, f"request line {i} wrong length {len(line)}"
for i, line in enumerate(resp_lines):
    assert len(line) == 2000, f"response line {i} wrong length {len(line)}"

with open("/home/claude/beq/mock/BEQ_Request_Sample.txt", "w") as f:
    f.write("\n".join(req_lines) + "\n")

with open("/home/claude/beq/mock/BEQ_Response_Sample.txt", "w") as f:
    f.write("\n".join(resp_lines) + "\n")

print(f"\nWrote {len(req_lines)} request records and {len(resp_lines)} response records.")
