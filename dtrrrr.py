import pandas as pd

# ---------------------------------------------------------------------------
# Source: MAPD Plan Communication User Guide (PCUG) v19.4, September 2026
#   - Layout 3-23: DTRR Data File Detail Record   (record length 800)
#   - Layout 3-9:  MARx Batch Input Detail Record: Enrollment - TC 61
#                  (record length 600)
#
# IMPORTANT: v19.4's own Change Log only mentions one edit to these layouts
# ("Updated Item 10 Position to 47-51 in Layout 3-9"). Direct inspection of
# the actual field tables shows the Change Log under-reported the real
# differences from v18.6. Verified directly against the source PDF text:
#
#   DTRR (Layout 3-23): 500 bytes (v18.6) -> 800 bytes (v19.4)
#     - Item 47 (189-195), "Ethnicity" in v18.6, is Filler in v19.4.
#     - Item 92 (456-474), "Race" in v18.6, is Filler in v19.4.
#     - Item 93 "System Assigned Transaction Tracking ID": 11 bytes (v18.6)
#       -> 20 bytes (v19.4), position 475-494.
#     - Item 94 "Plan Assigned Transaction Tracking ID": shifted to 495-509.
#     - Items 95-101 (Relationship to enrollee, National Producer Number,
#       OEC Indicator/Date/Number, Beneficiary Phone, Beneficiary Email)
#       are NEW in v19.4 -- they did not exist in v18.6.
#     - Item 102: Filler, 632-800.
#
#   TC 61 (Layout 3-9): 300 bytes (v18.6) -> 600 bytes (v19.4)
#     - Item 27 (103-123 in v19.4), "Race" in v18.6 (103-118), is Filler
#       in v19.4 (spans the old Race + old filler positions).
#     - Item 30 (126-134 in v19.4), "Ethnicity" in v18.6 (126-132), is
#       Filler in v19.4.
#     - Items 45-51 (Relationship to enrollee, National Producer Number,
#       OEC Indicator/Date/Number, Beneficiary Phone, Beneficiary Email)
#       are NEW in v19.4, at positions 292-413.
#     - Item 52: Filler, 414-600.
# ---------------------------------------------------------------------------

DTRR_FIELD_SPECS = [
    # (name,                                     start, length, kind)
    ("beneficiary_id",                              1,  12, "text"),
    ("surname",                                    13,  12, "text"),
    ("first_name",                                 25,   7, "text"),
    ("middle_initial",                             32,   1, "text"),
    ("sex_code",                                   33,   1, "text"),
    ("date_of_birth",                              34,   8, "date"),
    ("record_type",                                42,   1, "text"),
    ("contract_number",                            43,   5, "text"),
    ("state_code",                                 48,   2, "text"),
    ("county_code",                                50,   3, "text"),
    ("disability_indicator",                       53,   1, "text"),
    ("hospice_indicator",                          54,   1, "text"),
    ("institutional_nhc_hcbs_indicator",           55,   1, "text"),
    ("esrd_indicator",                             56,   1, "text"),
    ("trc",                                        57,   3, "text"),
    ("tc",                                         60,   2, "text"),
    ("entitlement_type_code",                      62,   1, "text"),
    ("effective_date",                             63,   8, "date"),
    ("wa_indicator",                               71,   1, "text"),
    ("pbp_id",                                     72,   3, "text"),
    ("filler_75",                                  75,   1, "text"),
    ("transaction_date",                           76,   8, "date"),
    ("ui_initiated_change_flag",                   84,   1, "text"),
    ("item24_trc_dependent",                       85,  12, "text"),
    ("district_office_code",                       97,   3, "text"),
    ("prev_part_d_contract_pbp",                  100,   8, "text"),
    ("sep_reason_code",                           108,   2, "text"),
    ("filler_110",                                110,   6, "text"),
    ("source_id",                                 116,   5, "text"),
    ("prior_pbp_id",                              121,   3, "text"),
    ("application_date",                          124,   8, "date"),
    ("ui_user_org_designation",                   132,   2, "text"),
    ("out_of_area_flag",                          134,   1, "text"),
    ("segment_number",                            135,   3, "text"),
    ("part_c_premium",                            138,   8, "num"),
    ("part_d_premium",                            146,   8, "num"),
    ("election_type_code",                        154,   1, "text"),
    ("enrollment_source_code",                    155,   1, "text"),
    ("part_d_opt_out_flag",                       156,   1, "text"),
    ("premium_withhold_option",                   157,   1, "text"),
    ("cumulative_uncovered_months",               158,   3, "num"),
    ("creditable_coverage_flag",                  161,   1, "text"),
    ("employer_subsidy_override_flag",            162,   1, "text"),
    ("processing_timestamp",                      163,  15, "text"),
    ("end_date",                                  178,   8, "date"),
    ("submitted_uncovered_months",                186,   3, "num"),
    ("filler_189",                                189,   7, "text"),   # Ethnicity in v18.6; filler in v19.4
    ("preferred_language_other_than_english",     196,   1, "text"),
    ("accessible_format",                         197,   1, "text"),
    ("secondary_drug_insurance_flag",             198,   1, "text"),
    ("secondary_rx_id",                           199,  20, "text"),
    ("secondary_rx_group",                        219,  15, "text"),
    ("eghp",                                      234,   1, "text"),
    ("part_d_lips_level",                         235,   3, "text"),
    ("low_income_copay_category",                 238,   1, "text"),
    ("low_income_period_effective_date",          239,   8, "date"),
    ("part_d_lep_amount",                         247,   8, "text"),
    ("part_d_lep_waived_amount",                  255,   8, "text"),
    ("part_d_lep_subsidy_amount",                 263,   8, "text"),
    ("low_income_part_d_premium_subsidy",         271,   8, "text"),
    ("part_d_rx_bin",                             279,   6, "text"),
    ("part_d_rx_pcn",                             285,  10, "text"),
    ("part_d_rx_group",                           295,  15, "text"),
    ("part_d_rx_id",                              310,  20, "text"),
    ("secondary_rx_bin",                          330,   6, "text"),
    ("secondary_rx_pcn",                          336,  10, "text"),
    ("de_minimis_differential_amount",            346,   8, "text"),
    ("msp_status_flag",                           354,   1, "text"),
    ("low_income_period_end_date",                355,   8, "date"),
    ("low_income_subsidy_source_code",            363,   1, "text"),
    ("enrollee_type_flag_pbp_level",              364,   1, "text"),
    ("application_date_indicator",                365,   1, "text"),
    ("trc_short_name",                            366,  15, "text"),
    ("disenrollment_reason_code",                 381,   2, "text"),
    ("mmp_opt_out_flag",                          383,   1, "text"),
    ("cleanup_id",                                384,  10, "text"),
    ("cara_status_add_update_delete_flag",        394,   1, "text"),
    ("pos_drug_edit_status",                      395,   1, "text"),
    ("drug_class",                                396,   3, "text"),
    ("pos_drug_edit_code",                        399,   3, "text"),
    ("cara_status_notification_start_date",       402,   8, "date"),
    ("cara_status_implementation_start_date",     410,   8, "date"),
    ("cara_status_notification_end_date",         418,   8, "date"),
    ("hospice_provider_number",                   426,  13, "text"),
    ("ic_model_type_indicator",                   439,   2, "text"),
    ("ic_model_end_date_reason_code",             441,   2, "text"),
    ("ic_model_benefit_status",                   443,   2, "text"),
    ("updated_medicaid_status_community_raf",     445,   1, "text"),
    ("cara_status_implementation_end_date",       446,   8, "date"),
    ("prescriber_limitation",                     454,   1, "text"),
    ("pharmacy_limitation",                       455,   1, "text"),
    ("filler_456",                                456,  19, "text"),   # Race in v18.6; filler in v19.4
    ("system_assigned_transaction_tracking_id",   475,  20, "text"),   # 20 bytes in v19.4 (was 11)
    ("plan_assigned_transaction_tracking_id",     495,  15, "text"),   # shifted to 495 in v19.4
    ("relationship_agent",                        510,   1, "text"),  # NEW in v19.4
    ("relationship_broker",                       511,   1, "text"),
    ("relationship_ship_counselors",              512,   1, "text"),
    ("relationship_authorized_reps",              513,   1, "text"),
    ("relationship_other_third_parties",          514,   1, "text"),
    ("relationship_self",                         515,   1, "text"),
    ("relationship_form_left_blank",              516,   1, "text"),
    ("national_producer_number",                  517,  10, "text"),  # NEW in v19.4
    ("oec_indicator",                             527,   1, "text"),  # NEW in v19.4
    ("oec_application_date",                      528,   8, "date"),  # NEW in v19.4
    ("oec_application_number",                    536,  12, "text"),  # NEW in v19.4
    ("beneficiary_phone_number",                  548,  10, "text"),  # NEW in v19.4
    ("beneficiary_email_address",                 558,  74, "text"),  # NEW in v19.4
    ("filler_632",                                632, 169, "text"),
]

DTRR_RECORD_LENGTH = 800

TC61_FIELD_SPECS = [
    ("beneficiary_id",                              1,  12, "text"),
    ("surname",                                    13,  12, "text"),
    ("first_name",                                 25,   7, "text"),
    ("middle_initial",                             32,   1, "text"),
    ("sex_code",                                   33,   1, "text"),
    ("birth_date",                                 34,   8, "date"),
    ("eghp_flag",                                  42,   1, "text"),
    ("pbp_id",                                     43,   3, "text"),
    ("election_type_code",                         46,   1, "text"),
    ("contract_id",                                47,   5, "text"),
    ("application_date",                           52,   8, "date"),
    ("transaction_code",                           60,   2, "text"),
    ("filler_62",                                  62,   2, "text"),
    ("effective_date",                             64,   8, "date"),
    ("segment_id",                                 72,   3, "text"),
    ("filler_75",                                  75,   5, "text"),
    ("esrd_override",                              80,   1, "text"),
    ("premium_withhold_option",                    81,   1, "text"),
    ("part_c_premium_amount",                      82,   6, "num"),
    ("filler_88",                                  88,   6, "text"),
    ("creditable_coverage_flag",                   94,   1, "text"),
    ("number_of_uncovered_months",                 95,   3, "num"),
    ("employer_subsidy_override_flag",             98,   1, "text"),
    ("part_d_opt_out_flag",                        99,   1, "text"),
    ("filler_100",                                100,   1, "text"),
    ("election_type_sep_reason_code",             101,   2, "text"),
    ("filler_103",                                103,  21, "text"),  # Race in v18.6; filler in v19.4
    ("preferred_language_other_than_english",     124,   1, "text"),
    ("accessible_format",                         125,   1, "text"),
    ("filler_126",                                126,   9, "text"),  # Ethnicity in v18.6; filler in v19.4
    ("secondary_drug_insurance_flag",             135,   1, "text"),
    ("secondary_rx_id",                           136,  20, "text"),
    ("secondary_rx_group",                        156,  15, "text"),
    ("enrollment_source_code",                    171,   1, "text"),
    ("rolled_from_contract",                      172,   5, "text"),
    ("rolled_from_pbp",                           177,   3, "text"),
    ("filler_180",                                180,  30, "text"),
    ("plan_assigned_transaction_tracking_id",     210,  15, "text"),
    ("part_d_rx_bin",                             225,   6, "text"),
    ("part_d_rx_pcn",                             231,  10, "text"),
    ("part_d_rx_group",                           241,  15, "text"),
    ("part_d_rx_id",                              256,  20, "text"),
    ("secondary_drug_bin",                        276,   6, "text"),
    ("secondary_drug_pcn",                        282,  10, "text"),
    ("relationship_agent",                        292,   1, "text"),  # NEW in v19.4
    ("relationship_broker",                       293,   1, "text"),
    ("relationship_ship_counselors",              294,   1, "text"),
    ("relationship_authorized_reps",               295,   1, "text"),
    ("relationship_other_third_parties",          296,   1, "text"),
    ("relationship_self",                         297,   1, "text"),
    ("relationship_form_left_blank",              298,   1, "text"),
    ("national_producer_number",                  299,  10, "text"),  # NEW in v19.4
    ("oec_indicator",                             309,   1, "text"),  # NEW in v19.4
    ("oec_application_date",                      310,   8, "date"),  # NEW in v19.4
    ("oec_application_number",                    318,  12, "text"),  # NEW in v19.4
    ("beneficiary_phone_number",                  330,  10, "text"),  # NEW in v19.4
    ("beneficiary_email_address",                 340,  74, "text"),  # NEW in v19.4
    ("filler_414",                                414, 187, "text"),
]

TC61_RECORD_LENGTH = 600


def _parse_line(line, field_specs, record_length):
    line = line.rstrip("\n").ljust(record_length)
    record = {}
    for name, start, length, kind in field_specs:
        raw = line[start - 1:start - 1 + length]
        value = raw.strip()
        if kind == "num" and value:
            try:
                value = int(value)
            except ValueError:
                pass
        record[name] = value
    return record


def parse_dtrr_file(path: str) -> pd.DataFrame:
    records = []
    with open(path, "r", encoding="latin-1") as f:
        for line in f:
            if line.strip():
                records.append(_parse_line(line, DTRR_FIELD_SPECS, DTRR_RECORD_LENGTH))
    return pd.DataFrame(records)


def parse_tc61_file(path: str) -> pd.DataFrame:
    records = []
    with open(path, "r", encoding="latin-1") as f:
        for line in f:
            if line.strip():
                records.append(_parse_line(line, TC61_FIELD_SPECS, TC61_RECORD_LENGTH))
    return pd.DataFrame(records)


if __name__ == "__main__":
    for label, specs, length in [("DTRR", DTRR_FIELD_SPECS, DTRR_RECORD_LENGTH),
                                  ("TC61", TC61_FIELD_SPECS, TC61_RECORD_LENGTH)]:
        pos = 1
        ok = True
        for name, start, flen, kind in specs:
            if start != pos:
                print(f"{label}: gap/overlap before {name} (expected {pos}, got {start})")
                ok = False
            pos = start + flen - 1 + 1
        print(f"{label}: {len(specs)} fields, coverage 1-{pos-1} "
              f"(expected {length}) -> {'OK' if ok and pos-1 == length else 'MISMATCH'}")
