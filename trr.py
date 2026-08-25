import argparse
import csv
import sys

RECORD_LENGTH = 600
TC_START, TC_END = 60, 61  # 1-indexed positions of the Transaction Code

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
    ("effective_date",            64,  71),
    ("segment_id",                72,  74),
    ("esrd_override",             80,  80),
    ("ppo_parts_cd",              81,  81),
    ("part_c_premium",            82,  87),
    ("creditable_coverage_flag",  94,  94),
    ("nuncmo",                    95,  97),
    ("employer_subsidy_flag",     98,  98),
    ("part_d_opt_out_flag",       99,  99),
    ("sep_reason_code",           101, 102),
    ("preferred_language",        124, 124),
    ("accessible_format",         125, 125),
    ("secondary_drug_ins_flag",   135, 135),
    ("secondary_rx_id",           136, 155),
    ("secondary_rx_group",        156, 170),
    ("enrollment_source_code",    171, 171),
    ("rolled_from_contract",      172, 176),
    ("rolled_from_pbp",           177, 179),
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
]

FIELD_POS = {name: (start, end) for name, start, end in TC61_FIELDS}
