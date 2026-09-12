"""
EAF -> DTRR field conversions.

These are the fields that can't be copied straight across because the two
specs use different date formats, different code sets, different field
widths, or a different "shape" (one EAF field splitting into several DTRR
flags). Everything else can be assigned directly (dtrr['x'] = eaf['y']).
"""

from datetime import datetime


# ---------------------------------------------------------------------------
# 1. Dates: EAF uses MMDDYYYY, DTRR uses CCYYMMDD
# ---------------------------------------------------------------------------
def convert_date_mmddyyyy_to_ccyymmdd(value: str) -> str:
    """
    '07131936' (EAF, MMDDYYYY) -> '19360713' (DTRR, CCYYMMDD)
    Blank/missing dates pass through as 8 spaces, matching DTRR's
    "spaces if not applicable" convention.
    """
    if not value or not value.strip():
        return " " * 8
    value = value.strip()
    try:
        dt = datetime.strptime(value, "%m%d%Y")
    except ValueError:
        # EAF's documented fallback for a bad/missing date is 01011900
        dt = datetime.strptime("01011900", "%m%d%Y")
    return dt.strftime("%Y%m%d")


DATE_FIELDS = [
    "date_of_birth", "effective_date", "application_date", "transaction_date",
    "low_income_period_effective_date", "low_income_period_end_date",
    "oec_application_date",
]


# ---------------------------------------------------------------------------
# 2. Sex code: EAF M/F/U(letters) -> DTRR 1/2/0 (digits)
# ---------------------------------------------------------------------------
SEX_CODE_MAP = {
    "M": "1",   # Male
    "F": "2",   # Female
    "U": "0",   # Unknown
    "":  "0",
}

def convert_sex_code(eaf_gender: str) -> str:
    return SEX_CODE_MAP.get((eaf_gender or "").strip().upper(), "0")


# ---------------------------------------------------------------------------
# 3. OEC indicator: EAF ApplicationType (numeric, 4 = OEC/CMS) -> DTRR Y/N
# ---------------------------------------------------------------------------
def convert_oec_indicator(eaf_application_type: str) -> str:
    return "Y" if (eaf_application_type or "").strip() == "4" else "N"


# ---------------------------------------------------------------------------
# 4. EGHP: EAF "Yes"/"No" (word) -> DTRR single Y / space
# ---------------------------------------------------------------------------
def convert_eghp(eaf_eghp_flag: str) -> str:
    return "Y" if (eaf_eghp_flag or "").strip().lower() == "yes" else " "


# ---------------------------------------------------------------------------
# 5. Preferred language: EAF free-form code/abbreviation -> DTRR S/O/X
#    Adjust LANGUAGE_LOOKUP to match your actual EAF value set (this is a
#    starting point — confirm the real EAF code list before relying on it).
# ---------------------------------------------------------------------------
LANGUAGE_LOOKUP = {
    "ENG": " ",   # English -> no flag needed (space = not applicable)
    "SPA": "S",
    "ESP": "S",
    "1":   " ",   # placeholder: confirm what EAF's numeric codes mean
    "2":   "S",
    "REMOVE": "X",
}

def convert_language(eaf_language: str) -> str:
    key = (eaf_language or "").strip().upper()
    if key in LANGUAGE_LOOKUP:
        return LANGUAGE_LOOKUP[key]
    # Anything else non-English and non-Spanish -> "Other"
    return "O" if key else " "


# ---------------------------------------------------------------------------
# 6. Accessible format: EAF allows a comma-separated multi-select
#    ("Braille, Large Print"); DTRR holds exactly one character.
#    Priority order below is a placeholder — confirm business rule for which
#    format wins when multiple are submitted.
# ---------------------------------------------------------------------------
ACCESSIBLE_FORMAT_MAP = {
    "BRAILLE": "B",
    "LARGE PRINT": "L",
    "AUDIO CD": "A",
    "DATA CD": "D",
}
ACCESSIBLE_FORMAT_PRIORITY = ["BRAILLE", "LARGE PRINT", "AUDIO CD", "DATA CD"]

def convert_accessible_format(eaf_accessibility_format: str) -> str:
    if not eaf_accessibility_format or not eaf_accessibility_format.strip():
        return " "
    values = {v.strip().upper() for v in eaf_accessibility_format.split(",")}
    if "REMOVE" in values or "X" in values:
        return "X"
    for candidate in ACCESSIBLE_FORMAT_PRIORITY:
        if candidate in values:
            return ACCESSIBLE_FORMAT_MAP[candidate]
    return " "


# ---------------------------------------------------------------------------
# 7. Relationship to enrollee: EAF single numeric code (1-7) -> DTRR 7
#    separate Y/space flags (positions 95a-95g)
# ---------------------------------------------------------------------------
RELATIONSHIP_FLAG_ORDER = [
    "relationship_agent",                  # 1 = Agent
    "relationship_broker",                 # 2 = Broker
    "relationship_ship_counselors",        # 3 = SHIP counselors
    "relationship_authorized_reps",        # 4 = Authorized representatives
    "relationship_other_third_parties",    # 5 = Other (third parties)
    "relationship_self",                   # 6 = Self
    "relationship_form_left_blank",        # 7 = Form left blank
]

def convert_relationship_to_enrollee(eaf_relationship_code: str) -> dict:
    """Returns a dict of the 7 DTRR flag fields, each 'Y' or ' '."""
    flags = {name: " " for name in RELATIONSHIP_FLAG_ORDER}
    code = (eaf_relationship_code or "").strip()
    if code.isdigit() and 1 <= int(code) <= 7:
        flags[RELATIONSHIP_FLAG_ORDER[int(code) - 1]] = "Y"
    return flags


# ---------------------------------------------------------------------------
# 8. Fixed-width padding helpers
# ---------------------------------------------------------------------------
def pad_beneficiary_id(mbi: str) -> str:
    """EAF MBI (up to 15 chars) -> DTRR 12-char field: 11-char MBI + 1 space."""
    mbi = (mbi or "").strip()[:11]
    return mbi.ljust(12)

def zero_pad(value: str, width: int) -> str:
    value = (value or "").strip()
    return value.zfill(width) if value.isdigit() else value.rjust(width)


# ---------------------------------------------------------------------------
# Putting it together: build the full DTRR record from an EAF record
# ---------------------------------------------------------------------------
def eaf_to_dtrr(eaf: dict) -> dict:
    dtrr = {}

    # --- direct copies (no conversion needed) ---
    dtrr['surname']          = eaf['member_last_name']
    dtrr['first_name']       = eaf['member_first_name']
    dtrr['middle_initial']   = eaf['member_middle_initial']
    dtrr['contract_number']  = eaf['contract_id']
    dtrr['state_code']       = eaf['member_state']
    dtrr['sep_reason_code']  = eaf['sep_reason_code']
    dtrr['election_type_code'] = eaf['election_type']
    dtrr['tc']               = eaf['transaction_type']
    dtrr['esrd_indicator']   = eaf['esrd']
    dtrr['part_d_opt_out_flag'] = eaf['part_d_opt_out']

    # --- date conversions ---
    dtrr['date_of_birth']    = convert_date_mmddyyyy_to_ccyymmdd(eaf['member_birth_date'])
    dtrr['effective_date']   = convert_date_mmddyyyy_to_ccyymmdd(eaf['effective_date'])
    dtrr['application_date'] = convert_date_mmddyyyy_to_ccyymmdd(eaf['application_sign_date'])
    dtrr['transaction_date'] = convert_date_mmddyyyy_to_ccyymmdd(eaf['submit_date'])
    dtrr['low_income_period_effective_date'] = convert_date_mmddyyyy_to_ccyymmdd(eaf['lis_effective_date'])
    dtrr['low_income_period_end_date']       = convert_date_mmddyyyy_to_ccyymmdd(eaf['lis_term_date'])
    dtrr['oec_application_date'] = convert_date_mmddyyyy_to_ccyymmdd(eaf['submit_date'])

    # --- code conversions ---
    dtrr['sex_code']          = convert_sex_code(eaf['member_gender'])
    dtrr['oec_indicator']     = convert_oec_indicator(eaf['application_type'])
    dtrr['eghp']              = convert_eghp(eaf['eghp_flag'])
    dtrr['preferred_language_other_than_english'] = convert_language(eaf['language'])
    dtrr['accessible_format'] = convert_accessible_format(eaf['accessibility_format'])

    # --- one-to-many expansion ---
    dtrr.update(convert_relationship_to_enrollee(eaf['relationship_to_enrollee']))

    # --- padded / fixed-width fields ---
    dtrr['beneficiary_id']  = pad_beneficiary_id(eaf['mbi'])
    dtrr['pbp_id']          = zero_pad(eaf['pbp_id'], 3)
    dtrr['segment_number']  = zero_pad(eaf['segment_id'], 3)
    dtrr['national_producer_number'] = zero_pad(eaf['national_producer_number'], 10)

    return dtrr
