import re

def blank(n):
    return [' '] * n

def set_field(buf, start, end, value, pad_char=' ', justify='left'):
    """1-indexed inclusive positions."""
    width = end - start + 1
    value = str(value)
    if justify == 'left':
        value = value.ljust(width, pad_char)[:width]
    else:
        value = value.rjust(width, pad_char)[:width]
    buf[start-1:end] = list(value)

def record_to_str(buf):
    return ''.join(buf)

# ---------- Common values shared by request & response ----------
SENDING_ENTITY_REQ = "H1234"           # 5-position contract
SENDING_ENTITY_REQ_FIELD = SENDING_ENTITY_REQ.ljust(8)   # 8 chars, 3 spaces future use
FILE_CREATION_DATE = "20260809"
FILE_CONTROL_NUMBER = "000000001"      # 9 chars

# ============================================================
# 1. BEQ REQUEST FILE  (750-byte records)
# ============================================================

def build_request_header():
    buf = blank(750)
    set_field(buf, 1, 8, "MMABEQRH")
    set_field(buf, 9, 16, SENDING_ENTITY_REQ_FIELD)
    set_field(buf, 17, 24, FILE_CREATION_DATE)
    set_field(buf, 25, 33, FILE_CONTROL_NUMBER)
    # 34-750 filler spaces
    return record_to_str(buf)

def build_request_detail(beneficiary_id, dob, sex_code, seq_num):
    buf = blank(750)
    set_field(buf, 1, 5, "DTL01")
    set_field(buf, 6, 17, beneficiary_id)      # 12 chars
    # 18-26 filler spaces
    set_field(buf, 27, 34, dob)
    set_field(buf, 35, 35, sex_code)
    set_field(buf, 36, 42, seq_num, pad_char='0', justify='right')
    # 43-750 filler spaces
    return record_to_str(buf)

def build_request_trailer(record_count):
    buf = blank(750)
    set_field(buf, 1, 8, "MMABEQRT")
    set_field(buf, 9, 16, SENDING_ENTITY_REQ_FIELD)
    set_field(buf, 17, 24, FILE_CREATION_DATE)
    set_field(buf, 25, 33, FILE_CONTROL_NUMBER)
    set_field(buf, 34, 40, str(record_count), pad_char='0', justify='right')
    # 41-750 filler spaces
    return record_to_str(buf)

# ---------- 3 mock beneficiaries for the request ----------
beneficiaries = [
    dict(id="1EG4TE5MK73 ", dob="19450612", sex="1", seq="0000001"),  # John A Smith - will match
    dict(id="2AB6CD7EF89 ", dob="19501203", sex="2", seq="0000002"),  # Mary J Johnson - will match
    dict(id="3XY9ZZ1AB23 ", dob="19380425", sex="1", seq="0000003"),  # Robert L Davis - will NOT match
]

req_lines = [build_request_header()]
for b in beneficiaries:
    req_lines.append(build_request_detail(b["id"], b["dob"], b["sex"], b["seq"]))
req_lines.append(build_request_trailer(len(beneficiaries)))

with open("/home/claude/beq/mock/BEQ_Request_Sample.txt", "w") as f:
    f.write("\n".join(req_lines) + "\n")

# Sanity check lengths
for i, line in enumerate(req_lines):
    assert len(line) == 750, f"request line {i} wrong length {len(line)}"

print("Request file OK:", len(req_lines), "records")

# ============================================================
# 2. BEQ RESPONSE FILE  (2000-byte records)
# ============================================================

def build_response_header():
    buf = blank(2000)
    set_field(buf, 1, 8, "CMSBEQRH")
    set_field(buf, 9, 16, "MBD".ljust(8))     # 'MBD ' + spaces = 8 chars
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

def build_response_detail(orig, matched, extra=None):
    """orig: dict with id/dob/sex/seq echoed from the request.
       matched: bool -> Processed Flag / Beneficiary Match Flag Y or N.
       extra: dict of beneficiary data fields to populate when matched.
    """
    buf = blank(2000)
    # --- Echoed original detail record (Fields 1-7) ---
    set_field(buf, 1, 3, "DTL")
    set_field(buf, 4, 8, "01   ")                  # rest of original 5-char record type, space filled
    set_field(buf, 9, 20, orig["id"])               # 12 chars
    # 21-29 filler spaces
    set_field(buf, 30, 37, orig["dob"])
    set_field(buf, 38, 38, orig["sex"])
    set_field(buf, 39, 45, orig["seq"], pad_char='0', justify='right')

    # --- Processing flags ---
    set_field(buf, 46, 46, "Y" if matched else "N")
    set_field(buf, 47, 47, "Y" if matched else "N")

    if matched and extra:
        set_field(buf, 48, 55, extra.get("partA_start", ""))
        set_field(buf, 56, 63, extra.get("partA_end", ""))
        set_field(buf, 64, 71, extra.get("partB_start", ""))
        set_field(buf, 72, 79, extra.get("partB_end", ""))
        set_field(buf, 80, 80, extra.get("medicaid_ind", "0"))

        # Sending Entity / File Control / Creation Date echoed back (Fields 35-37)
        set_field(buf, 241, 248, SENDING_ENTITY_REQ_FIELD)
        set_field(buf, 249, 257, FILE_CONTROL_NUMBER)
        set_field(buf, 258, 265, FILE_CREATION_DATE)
        set_field(buf, 266, 273, extra.get("partD_elig_start", ""))

        # LIS occurrence 1 (Fields 39-42)
        if extra.get("lis"):
            lis = extra["lis"]
            set_field(buf, 274, 281, lis.get("start", ""))
            set_field(buf, 282, 289, lis.get("end", ""))
            set_field(buf, 290, 290, lis.get("copay_level", ""))
            set_field(buf, 291, 293, lis.get("premium_pct", ""))

        # Beneficiary retrieved DOB/Sex (Fields 80-81), Name (82-84)
        set_field(buf, 624, 631, orig["dob"])
        set_field(buf, 632, 632, orig["sex"])
        set_field(buf, 633, 672, extra.get("last_name", ""))
        set_field(buf, 673, 702, extra.get("first_name", ""))
        set_field(buf, 703, 703, extra.get("middle_initial", ""))
        set_field(buf, 704, 705, extra.get("state_code", ""))
        set_field(buf, 706, 708, extra.get("county_code", ""))
        # 709-716 date of death - left blank (living beneficiary)

        # Plan enrollment (Part C/D) — Fields 88-90
        if extra.get("contract"):
            c = extra["contract"]
            set_field(buf, 717, 721, c.get("number", ""))
            set_field(buf, 722, 729, c.get("start", ""))
            set_field(buf, 730, 730, c.get("partd_ind", ""))
            set_field(buf, 745, 745, extra.get("esrd_ind", "0"))
            set_field(buf, 746, 748, c.get("pbp", ""))
            set_field(buf, 749, 750, c.get("plan_type", ""))
            set_field(buf, 751, 751, c.get("eghp_ind", "N"))
            set_field(buf, 1496, 1496, c.get("enroll_source", ""))

        # Mailing address (Fields 101-110)
        if extra.get("mailing"):
            m = extra["mailing"]
            set_field(buf, 758, 797, m.get("line1", ""))
            set_field(buf, 998, 1037, m.get("city", ""))
            set_field(buf, 1038, 1039, m.get("state", ""))
            set_field(buf, 1040, 1048, m.get("zip", ""))
            set_field(buf, 1049, 1056, m.get("start", ""))

        # Active MBI (Field 174)
        set_field(buf, 1556, 1566, extra.get("active_mbi", ""))

    return record_to_str(buf)

responses = [
    dict(
        orig=beneficiaries[0], matched=True,
        extra=dict(
            partA_start="20100601", partA_end="", partB_start="20100601", partB_end="",
            medicaid_ind="0", partD_elig_start="20100601",
            last_name="SMITH", first_name="JOHN", middle_initial="A",
            state_code="MD", county_code="003",
            contract=dict(number="H1234", start="20240101", partd_ind="Y",
                           pbp="001", plan_type="01", eghp_ind="N", enroll_source="B"),
            mailing=dict(line1="100 MAIN ST", city="BALTIMORE", state="MD",
                         zip="212010000", start="20240101"),
            active_mbi="1EG4TE5MK73",
        ),
    ),
    dict(
        orig=beneficiaries[1], matched=True,
        extra=dict(
            partA_start="20150301", partA_end="", partB_start="20150301", partB_end="",
            medicaid_ind="1", partD_elig_start="20150301",
            lis=dict(start="20260101", end="20261231", copay_level="1", premium_pct="100"),
            last_name="JOHNSON", first_name="MARY", middle_initial="J",
            state_code="VA", county_code="059",
            contract=dict(number="H5678", start="20230101", partd_ind="Y",
                           pbp="002", plan_type="29", eghp_ind="N", enroll_source="B"),
            mailing=dict(line1="200 OAK AVE", city="ARLINGTON", state="VA",
                         zip="222010000", start="20230101"),
            active_mbi="2AB6CD7EF89",
        ),
    ),
    dict(orig=beneficiaries[2], matched=False, extra=None),  # no match found
]

resp_lines = [build_response_header()]
for r in responses:
    resp_lines.append(build_response_detail(r["orig"], r["matched"], r["extra"]))
resp_lines.append(build_response_trailer(len(responses)))

with open("/home/claude/beq/mock/BEQ_Response_Sample.txt", "w") as f:
    f.write("\n".join(resp_lines) + "\n")

for i, line in enumerate(resp_lines):
    assert len(line) == 2000, f"response line {i} wrong length {len(line)}"

print("Response file OK:", len(resp_lines), "records")
