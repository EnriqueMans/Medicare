"""
DTRR (Daily Transaction Reply Report) generator - Transaction Code 61 (ROLLOVER)
Source: MA/PD Plan Communications User Guide v19.4 (August 2026), Layout 3-23:
        "DTRR Data File Detail Record" - MARx Data File, 800-byte fixed-width record.

TC 61 = ROLLOVER (Plan-submitted rollover / PBP change enrollment transaction).

HOW TO USE
----------
1. Edit COLUMN_MAP below so the right-hand side matches the actual column
   names in your `df_data` DataFrame. Any field left mapped to None will be
   written as spaces (or zeros, for a couple of numeric-looking fields).
2. Run this script (or paste the functions into your notebook) with df_data
   already loaded in memory.
3. Output is a fixed-width .txt file, one 800-byte record per row, matching
   the CMS DTRR Detail Record layout, with Transaction Code hard-coded to 61.

NOTES ON SCOPE
--------------
The DTRR Detail Record layout is generic across all Transaction Reply Codes
(TRCs); many of its 100+ items are only populated for specific TRCs. This
script populates:
  - All fields that are always present (beneficiary demographics, contract,
    dates, etc.)
  - All fields the Guide specifically calls out as TC-61-specific:
      Item 30  Prior Plan Benefit Package ID   (pos 121-123)
      Item 48  Preferred Language Other Than English (pos 196)
      Item 49  Accessible Format               (pos 197)
      Item 50  Secondary Drug Insurance Flag    (pos 198)
      Item 51  Secondary Rx ID                  (pos 199-218)
      Item 52  Secondary Rx Group               (pos 219-233)
      Item 53  EGHP                             (pos 234)
      Item 61  Part D Rx BIN                    (pos 279-284)
      Item 62  Part D Rx PCN                    (pos 285-294)
      Item 63  Part D Rx Group                  (pos 295-309)
      Item 64  Part D Rx ID                     (pos 310-329)
      Item 65  Secondary Rx BIN                 (pos 330-335)
      Item 66  Secondary Rx PCN                 (pos 336-345)
      Item 95  Relationship to Enrollee (a-g)    (pos 510-516)
      Item 96  National Producer Number (NPN)   (pos 517-526)
      Item 97-99  OEC Indicator/Date/App Number (pos 527-547)
      Item 100 Beneficiary Phone Number          (pos 548-557)
      Item 101 Beneficiary Email Address         (pos 558-631)

Fields whose content is TRC-dependent (Item 24 sub-fields a-gg) are left as
spaces by default since they depend on the specific TRC returned, not on
TC=61 alone. If you need one of those populated, add it to COLUMN_MAP and
FIELD_SPECS following the same pattern.
"""

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# 1. FIELD SPEC: (name, start_pos, length) -- 1-indexed positions, per Layout 3-23
#    "kind" controls formatting: 'text' (left-justified, space-padded),
#    'num' (right-justified, zero-padded), 'date' (CCYYMMDD, spaces if blank)
# ---------------------------------------------------------------------------
FIELD_SPECS = [
    # (name,                                  start, length, kind)
    ("beneficiary_id",                          1,  12, "text"),
    ("surname",                                13,  12, "text"),
    ("first_name",                             25,   7, "text"),
    ("middle_initial",                         32,   1, "text"),
    ("sex_code",                               33,   1, "text"),   # 0/1/2
    ("date_of_birth",                          34,   8, "date"),
    ("record_type",                            42,   1, "text"),   # 'T' = TRC record
    ("contract_number",                        43,   5, "text"),
    ("state_code",                             48,   2, "text"),
    ("county_code",                            50,   3, "text"),
    ("disability_indicator",                   53,   1, "text"),
    ("hospice_indicator",                      54,   1, "text"),
    ("institutional_nhc_hcbs_indicator",       55,   1, "text"),
    ("esrd_indicator",                         56,   1, "text"),
    ("trc",                                    57,   3, "text"),   # Transaction Reply Code
    ("tc",                                     60,   2, "text"),   # Transaction Code -> hard-coded '61'
    ("entitlement_type_code",                  62,   1, "text"),
    ("effective_date",                         63,   8, "date"),
    ("wa_indicator",                           71,   1, "text"),
    ("pbp_id",                                 72,   3, "text"),
    ("filler_75",                              75,   1, "text"),
    ("transaction_date",                       76,   8, "date"),
    ("ui_initiated_change_flag",               84,   1, "text"),
    # Item 24 (TRC-dependent sub-fields) left blank -> positions 85-96
    ("item24_trc_dependent",                   85,  12, "text"),
    ("district_office_code",                   97,   3, "text"),
    ("prev_part_d_contract_pbp",              100,   8, "text"),
    ("sep_reason_code",                       108,   2, "text"),
    ("filler_110",                            110,   6, "text"),
    ("source_id",                             116,   5, "text"),
    ("prior_pbp_id",                          121,   3, "text"),   # Item 30: TC 61 only
    ("application_date",                      124,   8, "date"),
    ("ui_user_org_designation",               132,   2, "text"),
    ("out_of_area_flag",                      134,   1, "text"),
    ("segment_number",                        135,   3, "text"),
    ("part_c_premium",                        138,   8, "num"),
    ("part_d_premium",                        146,   8, "num"),
    ("election_type_code",                    154,   1, "text"),
    ("enrollment_source_code",                155,   1, "text"),
    ("part_d_opt_out_flag",                   156,   1, "text"),
    ("premium_withhold_option",               157,   1, "text"),
    ("cumulative_uncovered_months",           158,   3, "num"),
    ("creditable_coverage_flag",              161,   1, "text"),
    ("employer_subsidy_override_flag",        162,   1, "text"),
    ("processing_timestamp",                  163,  15, "text"),
    ("end_date",                              178,   8, "date"),
    ("submitted_uncovered_months",            186,   3, "num"),
    ("filler_189",                            189,   7, "text"),
    ("preferred_language_other_than_english", 196,   1, "text"),   # Item 48: TC 61/92
    ("accessible_format",                     197,   1, "text"),   # Item 49: TC 61/92
    ("secondary_drug_insurance_flag",         198,   1, "text"),   # Item 50: TC 61/72
    ("secondary_rx_id",                       199,  20, "text"),   # Item 51: TC 61/72
    ("secondary_rx_group",                    219,  15, "text"),   # Item 52: TC 61/72
    ("eghp",                                  234,   1, "text"),   # Item 53: TC 61 -> Y or space
    ("part_d_lips_level",                     235,   3, "text"),
    ("low_income_copay_category",             238,   1, "text"),
    ("low_income_period_effective_date",      239,   8, "date"),
    ("part_d_lep_amount",                     247,   8, "text"),
    ("part_d_lep_waived_amount",              255,   8, "text"),
    ("part_d_lep_subsidy_amount",             263,   8, "text"),
    ("low_income_part_d_premium_subsidy",     271,   8, "text"),
    ("part_d_rx_bin",                         279,   6, "text"),   # Item 61: TC 61/72
    ("part_d_rx_pcn",                         285,  10, "text"),   # Item 62: TC 61/72
    ("part_d_rx_group",                       295,  15, "text"),   # Item 63: TC 61/72
    ("part_d_rx_id",                          310,  20, "text"),   # Item 64: TC 61/72
    ("secondary_rx_bin",                      330,   6, "text"),   # Item 65: TC 61/72
    ("secondary_rx_pcn",                      336,  10, "text"),   # Item 66: TC 61/72
    ("de_minimis_differential_amount",        346,   8, "text"),
    ("msp_status_flag",                       354,   1, "text"),
    ("low_income_period_end_date",            355,   8, "date"),
    ("low_income_subsidy_source_code",        363,   1, "text"),
    ("enrollee_type_flag_pbp_level",          364,   1, "text"),
    ("application_date_indicator",            365,   1, "text"),
    ("trc_short_name",                        366,  15, "text"),
    ("disenrollment_reason_code",             381,   2, "text"),
    ("mmp_opt_out_flag",                      383,   1, "text"),
    ("cleanup_id",                            384,  10, "text"),
    ("cara_status_add_update_delete_flag",    394,   1, "text"),
    ("pos_drug_edit_status",                  395,   1, "text"),
    ("drug_class",                            396,   3, "text"),
    ("pos_drug_edit_code",                    399,   3, "text"),
    ("cara_status_notification_start_date",   402,   8, "date"),
    ("cara_status_implementation_start_date", 410,   8, "date"),
    ("cara_status_notification_end_date",     418,   8, "date"),
    ("hospice_provider_number",               426,  13, "text"),
    ("ic_model_type_indicator",               439,   2, "text"),
    ("ic_model_end_date_reason_code",         441,   2, "text"),
    ("ic_model_benefit_status",               443,   2, "text"),
    ("updated_medicaid_status_community_raf", 445,   1, "text"),
    ("cara_status_implementation_end_date",   446,   8, "date"),
    ("prescriber_limitation",                 454,   1, "text"),
    ("pharmacy_limitation",                   455,   1, "text"),
    ("filler_456",                            456,  19, "text"),
    ("system_assigned_transaction_tracking_id", 475, 20, "text"),
    ("plan_assigned_transaction_tracking_id", 495,  15, "text"),
    ("relationship_agent",                    510,   1, "text"),   # Item 95a: TC 61/92
    ("relationship_broker",                   511,   1, "text"),   # Item 95b
    ("relationship_ship_counselors",          512,   1, "text"),   # Item 95c
    ("relationship_authorized_reps",          513,   1, "text"),   # Item 95d
    ("relationship_other_third_parties",      514,   1, "text"),   # Item 95e
    ("relationship_self",                     515,   1, "text"),   # Item 95f
    ("relationship_form_left_blank",          516,   1, "text"),   # Item 95g
    ("national_producer_number",              517,  10, "text"),   # Item 96
    ("oec_indicator",                         527,   1, "text"),   # Item 97
    ("oec_application_date",                  528,   8, "date"),   # Item 98
    ("oec_application_number",                536,  12, "text"),   # Item 99
    ("beneficiary_phone_number",              548,  10, "text"),   # Item 100
    ("beneficiary_email_address",             558,  74, "text"),   # Item 101
    # Item 102 filler 632-800 -> left as spaces automatically
]

RECORD_LENGTH = 800

# ---------------------------------------------------------------------------
# 2. COLUMN MAP: EDIT THE RIGHT-HAND SIDE to match your df_data column names.
#    Set to None for fields you don't have data for (they'll be blank/spaces).
# ---------------------------------------------------------------------------
COLUMN_MAP = {
    "beneficiary_id":                          "beneficiary_id",      # or "mbi" / "hicn"
    "surname":                                 "surname",
    "first_name":                              "first_name",
    "middle_initial":                          "middle_initial",
    "sex_code":                                "sex_code",
    "date_of_birth":                           "date_of_birth",
    "record_type":                             None,                  # defaults to 'T' below
    "contract_number":                         "contract_number",
    "state_code":                              "state_code",
    "county_code":                             "county_code",
    "disability_indicator":                    None,
    "hospice_indicator":                       None,
    "institutional_nhc_hcbs_indicator":        None,
    "esrd_indicator":                          None,
    "trc":                                     "trc",                 # Transaction Reply Code
    "tc":                                      None,                  # forced to '61' below
    "entitlement_type_code":                   None,
    "effective_date":                          "effective_date",
    "wa_indicator":                            None,
    "pbp_id":                                  "pbp_id",
    "transaction_date":                        "transaction_date",
    "ui_initiated_change_flag":                None,
    "district_office_code":                    None,
    "prev_part_d_contract_pbp":                None,
    "sep_reason_code":                         "sep_reason_code",
    "source_id":                               "source_id",
    "prior_pbp_id":                            "prior_pbp_id",        # Item 30, TC 61-specific
    "application_date":                        "application_date",
    "ui_user_org_designation":                 None,
    "out_of_area_flag":                        None,
    "segment_number":                          "segment_number",
    "part_c_premium":                          "part_c_premium",
    "part_d_premium":                          "part_d_premium",
    "election_type_code":                      "election_type_code",
    "enrollment_source_code":                  "enrollment_source_code",
    "part_d_opt_out_flag":                     "part_d_opt_out_flag",
    "premium_withhold_option":                 "premium_withhold_option",
    "cumulative_uncovered_months":             "cumulative_uncovered_months",
    "creditable_coverage_flag":                "creditable_coverage_flag",
    "employer_subsidy_override_flag":          "employer_subsidy_override_flag",
    "processing_timestamp":                    None,
    "end_date":                                None,
    "submitted_uncovered_months":              None,
    "preferred_language_other_than_english":   "preferred_language",
    "accessible_format":                       "accessible_format",
    "secondary_drug_insurance_flag":           "secondary_drug_insurance_flag",
    "secondary_rx_id":                         "secondary_rx_id",
    "secondary_rx_group":                      "secondary_rx_group",
    "eghp":                                    "eghp",
    "part_d_lips_level":                       None,
    "low_income_copay_category":               None,
    "low_income_period_effective_date":        None,
    "part_d_lep_amount":                       None,
    "part_d_lep_waived_amount":                None,
    "part_d_lep_subsidy_amount":               None,
    "low_income_part_d_premium_subsidy":       None,
    "part_d_rx_bin":                           "part_d_rx_bin",
    "part_d_rx_pcn":                           "part_d_rx_pcn",
    "part_d_rx_group":                         "part_d_rx_group",
    "part_d_rx_id":                            "part_d_rx_id",
    "secondary_rx_bin":                        "secondary_rx_bin",
    "secondary_rx_pcn":                        "secondary_rx_pcn",
    "de_minimis_differential_amount":          None,
    "msp_status_flag":                         None,
    "low_income_period_end_date":              None,
    "low_income_subsidy_source_code":          None,
    "enrollee_type_flag_pbp_level":            None,
    "application_date_indicator":              None,
    "trc_short_name":                          None,
    "disenrollment_reason_code":               None,
    "mmp_opt_out_flag":                        None,
    "cleanup_id":                              None,
    "cara_status_add_update_delete_flag":      None,
    "pos_drug_edit_status":                    None,
    "drug_class":                              None,
    "pos_drug_edit_code":                      None,
    "cara_status_notification_start_date":     None,
    "cara_status_implementation_start_date":   None,
    "cara_status_notification_end_date":       None,
    "hospice_provider_number":                 None,
    "ic_model_type_indicator":                 None,
    "ic_model_end_date_reason_code":           None,
    "ic_model_benefit_status":                 None,
    "updated_medicaid_status_community_raf":   None,
    "cara_status_implementation_end_date":     None,
    "prescriber_limitation":                   None,
    "pharmacy_limitation":                     None,
    "system_assigned_transaction_tracking_id": "system_tracking_id",
    "plan_assigned_transaction_tracking_id":   "plan_tracking_id",
    "relationship_agent":                      "relationship_agent",
    "relationship_broker":                     "relationship_broker",
    "relationship_ship_counselors":            "relationship_ship_counselors",
    "relationship_authorized_reps":            "relationship_authorized_reps",
    "relationship_other_third_parties":        "relationship_other_third_parties",
    "relationship_self":                       "relationship_self",
    "relationship_form_left_blank":            "relationship_form_left_blank",
    "national_producer_number":                "npn",
    "oec_indicator":                           "oec_indicator",
    "oec_application_date":                    "oec_application_date",
    "oec_application_number":                  "oec_application_number",
    "beneficiary_phone_number":                "phone_number",
    "beneficiary_email_address":               "email_address",
}


def _fmt(value, length, kind):
    """Format a single field's value to its fixed-width slot."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        text = ""
    else:
        text = str(value).strip()

    if kind == "date":
        if not text:
            return " " * length
        # Accept datetime-like or already-CCYYMMDD strings
        try:
            ts = pd.to_datetime(text)
            text = ts.strftime("%Y%m%d")
        except (ValueError, TypeError):
            text = text.replace("-", "").replace("/", "")
        return text.ljust(length)[:length]

    if kind == "num":
        if not text:
            return " " * length
        digits = "".join(ch for ch in text if ch.isdigit())
        return digits.rjust(length, "0")[-length:] if digits else " " * length

    # kind == 'text'
    return text.ljust(length)[:length]


def build_dtrr_record(row: dict) -> str:
    """Build a single 800-byte fixed-width DTRR record (dict) with TC forced to 61."""
    buf = [" "] * RECORD_LENGTH

    values = dict(row)
    values["tc"] = "61"                              # Transaction Code = 61 (Rollover)
    values.setdefault("record_type", None)
    if not values.get("record_type"):
        values["record_type"] = "T"                  # 'T' = TRC record

    for name, start, length, kind in FIELD_SPECS:
        val = values.get(name)
        formatted = _fmt(val, length, kind)
        buf[start - 1:start - 1 + length] = list(formatted)

    record = "".join(buf)
    assert len(record) == RECORD_LENGTH, f"Record length {len(record)} != {RECORD_LENGTH}"
    return record


def build_row_values(df_row: pd.Series) -> dict:
    """Map one df_data row to FIELD_SPECS names using COLUMN_MAP."""
    values = {}
    for field_name, col_name in COLUMN_MAP.items():
        if col_name and col_name in df_row.index:
            values[field_name] = df_row[col_name]
        else:
            values[field_name] = None
    return values


def generate_dtrr_file(df_data: pd.DataFrame, output_path: str) -> str:
    """
    Generate a DTRR fixed-width text file for TC 61 (Rollover) from df_data.
    Returns the output_path written.
    """
    missing_required = [c for c in ("beneficiary_id",) if COLUMN_MAP.get(c) not in df_data.columns]
    if missing_required:
        raise ValueError(
            f"df_data is missing required column(s) referenced in COLUMN_MAP: {missing_required}. "
            "Update COLUMN_MAP at the top of this script to match your DataFrame."
        )

    with open(output_path, "w", newline="\n") as f:
        for _, df_row in df_data.iterrows():
            values = build_row_values(df_row)
            record = build_dtrr_record(values)
            f.write(record + "\n")

    return output_path


if __name__ == "__main__":
    # Example / smoke test with a tiny synthetic DataFrame.
    # Replace this block with your real df_data when importing into a notebook,
    # or simply delete this __main__ block and call generate_dtrr_file(df_data, ...) directly.
    df_data = pd.DataFrame([
        {
            "beneficiary_id": "1EG4TE5MK73",
            "surname": "SMITH",
            "first_name": "JOHN",
            "middle_initial": "Q",
            "sex_code": "1",
            "date_of_birth": "1950-04-12",
            "contract_number": "H1234",
            "state_code": "36",
            "county_code": "005",
            "trc": "191",
            "effective_date": "2026-09-01",
            "pbp_id": "001",
            "transaction_date": "2026-08-29",
            "prior_pbp_id": "002",
            "election_type_code": "C",
            "enrollment_source_code": "N",
            "eghp": " ",
        },
    ])

    out = generate_dtrr_file(df_data, "/mnt/user-data/outputs/dtrr_tc61_rollover_output.txt")
    print(f"Wrote {len(df_data)} record(s) to {out}")
