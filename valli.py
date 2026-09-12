"""
EAF -> DTRR field value converter (TC 61 focus)

Takes a parsed EAF record (a dict keyed by the eaf_dtrr_mapping.eaf keys,
e.g. {"mbi": "1EG4TE5MK73", "member_gender": "M", ...}) and produces the
corresponding DTRR field values (keyed by dtrr keys), applying the value
transformations needed for the fields that aren't a straight copy:

  - Dates: EAF uses MMDDYYYY: DTRR uses CCYYMMDD.
  - Gender: EAF uses M/F: DTRR Sex Code uses 1=Male/2=Female/0=Unknown.
  - Everything else in MAPPING is copied through as-is (already the same
    code set/format on both sides), unless overridden below.

Only fields present in eaf_dtrr_mapping.MAPPING are converted - that's the
set of EAF columns known to have a documented DTRR counterpart. Fields not
in MAPPING (e.g. free-text addresses, bank info, plan-defined elements)
have no DTRR reply equivalent and are skipped.
"""

import re
from eaf_dtrr_mapping import eaf, dtrr, MAPPING, MAPPING_DETAILS

DATE_FIELDS_MMDDYYYY = {
    "member_birth_date",
    "application_sign_date",
    "effective_date",
    "lis_effective_date",
    "lis_term_date",
    "mppp_termination_date",
}

GENDER_MAP = {"M": "1", "F": "2", "U": "0", "": ""}


def _convert_date_mmddyyyy_to_ccyymmdd(value: str) -> str:
    """MMDDYYYY -> CCYYMMDD. Returns the value unchanged if it doesn't
    look like a clean 8-digit MMDDYYYY date (e.g. blank/space-filled)."""
    if not value or not re.match(r'^\d{8}$', value):
        return value
    mm, dd, yyyy = value[0:2], value[2:4], value[4:8]
    return f"{yyyy}{mm}{dd}"


def _convert_gender(value: str) -> str:
    return GENDER_MAP.get((value or "").strip().upper(), value)


# eaf_key -> transform function(value) -> converted value.
# Any eaf_key in MAPPING not listed here is copied through unchanged.
FIELD_TRANSFORMS = {
    "member_gender": _convert_gender,
}
for _key in DATE_FIELDS_MMDDYYYY:
    FIELD_TRANSFORMS[_key] = _convert_date_mmddyyyy_to_ccyymmdd


def convert_eaf_to_dtrr(eaf_record: dict, include_unmapped_as_none: bool = False):
    """
    Convert an EAF record's mapped fields into their DTRR equivalents.

    eaf_record: dict of {eaf_key: value}, e.g. output of parsing an EAF row
                using the eaf_dtrr_mapping.eaf keys as column names.
    include_unmapped_as_none: if True, also include every mapped dtrr_key
                even when the eaf_record didn't supply a value (as None).

    Returns: (dtrr_record: dict, notes: list[str])
        dtrr_record is {dtrr_key: converted_value}
        notes lists any conditional/loose mappings that were applied, so
        the caller can flag them for review rather than trusting a blind
        copy (see MAPPING_DETAILS confidence levels).
    """
    dtrr_record = {}
    notes = []

    for eaf_key, dtrr_key in MAPPING.items():
        if eaf_key not in eaf_record:
            if include_unmapped_as_none:
                dtrr_record[dtrr_key] = None
            continue

        raw_value = eaf_record[eaf_key]
        transform = FIELD_TRANSFORMS.get(eaf_key)
        value = transform(raw_value) if transform else raw_value
        dtrr_record[dtrr_key] = value

        detail = MAPPING_DETAILS.get(eaf_key, {})
        if detail.get("confidence") in ("conditional", "loose"):
            notes.append(
                f"{eaf_key} -> {dtrr_key} [{detail['confidence']}]: {detail['note']}"
            )

    return dtrr_record, notes


def convert_and_pack(eaf_record: dict):
    """
    Convert an EAF record and pack the result into a full 800-byte,
    space-padded DTRR Detail Record string using each field's documented
    byte position (from dtrr_tc61_field_validation.FIELD_SPECS).

    Only the fields covered by MAPPING are populated; every other position
    is left as spaces (MARx/CMS populates those from its own processing,
    not from a straight EAF copy).
    """
    from dtrr_tc61_field_validation import FIELD_SPECS, RECORD_LENGTH

    dtrr_values, notes = convert_eaf_to_dtrr(eaf_record)
    record = [' '] * RECORD_LENGTH

    for dtrr_key, value in dtrr_values.items():
        # find the field_id whose key matches dtrr_key
        matches = [fid for fid, meta in dtrr.items() if fid == dtrr_key]
        spec_key = dtrr_key
        field_id = dtrr[spec_key]["field_id"]
        spec = FIELD_SPECS.get(field_id)
        if spec is None or spec["position"][0] is None:
            continue
        start, end = spec["position"]
        size = end - start + 1
        text = "" if value is None else str(value)
        text = text[:size].ljust(size)
        record[start - 1:end] = list(text)

    return "".join(record), notes


if __name__ == "__main__":
    # Example: a minimal TC 61 EAF submission
    sample_eaf_record = {
        "mbi": "1EG4TE5MK73",
        "member_last_name": "SMITH",
        "member_first_name": "JOHN",
        "member_middle_initial": "Q",
        "member_gender": "M",
        "member_birth_date": "05151955",   # MMDDYYYY
        "contract_id": "H1234",
        "pbp_id": "001",
        "segment_id": "000",
        "effective_date": "01012026",      # MMDDYYYY
        "transaction_type": "61",
        "application_sign_date": "12152025",
        "language": "SPA",
        "eghp_flag": "Y",
    }

    converted, notes = convert_eaf_to_dtrr(sample_eaf_record)
    print("Converted DTRR fields:")
    for k, v in converted.items():
        print(f"  {k}: {v!r}")

    print("\nNotes (conditional/loose mappings used):")
    for n in notes:
        print(" -", n)

    packed, _ = convert_and_pack(sample_eaf_record)
    print("\nPacked record length:", len(packed))
    print(repr(packed[:40]), "...")
