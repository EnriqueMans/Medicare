"""
DTRR -> EAF field crosswalk, WITH conversions applied inline on the same
line as the assignment. Same field list/order as dtrr_to_eaf_assignments.py,
but every field that needs a value transform (not a straight copy) calls
the conversion helper right there instead of a bare assignment.

Requires: mmddyyyy_to_ccyymmdd, gender_to_sex, yes_no_to_flag,
language_to_flag, accessible_format_to_flag, election_type_to_code,
relationship_flag (defined below - same logic as eaf_dtrr_fit.py,
collected here so this file is self-contained and readable top to bottom).
"""

import re

# --- conversion helpers -----------------------------------------------

def mmddyyyy_to_ccyymmdd(value):
    """EAF dates are MMDDYYYY; DTRR dates are CCYYMMDD."""
    if not value or not re.match(r'^\d{8}$', value):
        return value
    mm, dd, yyyy = value[0:2], value[2:4], value[4:8]
    return f"{yyyy}{mm}{dd}"

def gender_to_sex(value):
    """EAF M/F -> DTRR Sex Code 1/2 (0 = Unknown)."""
    return {"M": "1", "F": "2"}.get((value or "").strip().upper(), "0")

def yes_no_to_flag(value):
    """EAF Yes/No -> DTRR Y/N (space if blank)."""
    return {"YES": "Y", "NO": "N", "Y": "Y", "N": "N"}.get((value or "").strip().upper(), " ")

def language_to_flag(value):
    """EAF language name/code -> DTRR S=Spanish/O=Other/X=remove/space flag.
    NOTE: EAF's Language field is itself a plan-defined code - resolve it to
    a name using your plan's language reference table before calling this."""
    key = (value or "").strip().upper()
    if key in ("SPANISH", "SPA", "ES"):
        return "S"
    if key in ("REMOVE", "X"):
        return "X"
    if key in ("ENGLISH", "ENG", ""):
        return " "
    return "O"

def accessible_format_to_flag(value):
    """EAF word -> DTRR B/L/A/D/X flag. Do not truncate - 'Remove' -> 'X', not 'R'."""
    return {
        "BRAILLE": "B", "LARGEPRINT": "L", "AUDIOCD": "A",
        "DATACD": "D", "REMOVE": "X",
    }.get((value or "").strip().upper(), " ")

def election_type_to_code(value):
    """EAF abbreviation -> DTRR single letter. BEST EFFORT - verify against
    your EAF Appendix 'Election Types' table."""
    return {
        "AEP": "A", "IEP": "E", "IEP2": "F", "ICEP": "I", "DEM": "J",
        "MAOEP": "M", "OEPNEW": "N", "OEP": "O", "OEPI": "T",
        "5STARSEP": "R", "PCR": "V", "EGHPSEP": "W", "AASEP": "X",
        "CMSSEP": "Y", "ROLLOVER": "C",
    }.get((value or "").strip().upper(), value)

def relationship_flag(value, code):
    """EAF relationship_to_enrollee (1-7) -> Y/N for one specific DTRR
    sub-flag. code: 1=agent, 2=broker, 3=SHIP, 4=auth rep, 5=other,
    6=self, 7=form left blank."""
    return "Y" if str(value).strip() == str(code) else "N"


# --- crosswalk, conversions applied inline -----------------------------

def build_dtrr_record(eaf):
    """eaf: dict of {eaf_key: value}. Returns dict of {dtrr_key: value}."""
    dtrr = {}

    dtrr['beneficiary_id']                          = eaf['mbi']                                              # Field 20
    dtrr['surname']                                  = eaf['member_last_name']                                # Field 9
    dtrr['first_name']                               = eaf['member_first_name']                               # Field 7
    dtrr['middle_initial']                           = eaf['member_middle_initial']                           # Field 8
    dtrr['sex_code']                                 = gender_to_sex(eaf['member_gender'])                    # Field 11, M/F -> 1/2
    dtrr['date_of_birth']                            = mmddyyyy_to_ccyymmdd(eaf['member_birth_date'])         # Field 10, MMDDYYYY -> CCYYMMDD
    dtrr['record_type']                              = None                                                   # DTRR-side only
    dtrr['contract_number']                          = eaf['contract_id']                                     # Field 3
    dtrr['state_code']                               = eaf['member_state']                                    # Field 16
    dtrr['county_code']                              = None                                                   # Not present on EAF
    dtrr['disability_indicator']                     = None                                                   # Not present on EAF
    dtrr['hospice_indicator']                        = None                                                   # Not present on EAF
    dtrr['institutional_nhc_hcbs_indicator']         = None                                                   # Not present on EAF
    dtrr['esrd_indicator']                           = yes_no_to_flag(eaf['esrd'])                            # Field 50, Yes/No -> Y/N (loose: system-determined on real replies)
    dtrr['trc']                                      = None                                                   # CMS-generated
    dtrr['tc']                                       = eaf['transaction_type']                                # Field 74
    dtrr['entitlement_type_code']                    = None                                                   # Not present on EAF
    dtrr['effective_date']                           = mmddyyyy_to_ccyymmdd(eaf['effective_date'])            # Field 73, MMDDYYYY -> CCYYMMDD
    dtrr['wa_indicator']                             = None                                                   # Not present on EAF
    dtrr['pbp_id']                                   = eaf['pbp_id']                                          # Field 4
    dtrr['filler_75']                                = None
    dtrr['transaction_date']                         = mmddyyyy_to_ccyymmdd(eaf['submit_date'])               # Field 2, MMDDYYYY -> CCYYMMDD
    dtrr['ui_initiated_change_flag']                 = None                                                   # System-generated
    dtrr['item24_trc_dependent']                     = None                                                   # CMS reply-side only
    dtrr['district_office_code']                     = None                                                   # Not present on EAF
    dtrr['prev_part_d_contract_pbp']                 = None                                                   # Not present on EAF
    dtrr['sep_reason_code']                          = eaf['sep_reason_code']                                 # Field 64
    dtrr['filler_110']                               = None
    dtrr['source_id']                                = eaf['sales_location']                                  # Field 80
    dtrr['prior_pbp_id']                             = None                                                   # Not present on EAF
    dtrr['application_date']                         = mmddyyyy_to_ccyymmdd(eaf['application_sign_date'])     # Field 75, MMDDYYYY -> CCYYMMDD
    dtrr['ui_user_org_designation']                  = None                                                   # Not present on EAF
    dtrr['out_of_area_flag']                         = None                                                   # Not present on EAF
    dtrr['segment_number']                           = eaf['segment_id']                                      # Field 5
    dtrr['part_c_premium']                           = None                                                   # CMS-calculated
    dtrr['part_d_premium']                           = None                                                   # CMS-calculated
    dtrr['election_type_code']                       = election_type_to_code(eaf['election_type'])            # Field 78, AEP/OEP/... -> single letter
    dtrr['enrollment_source_code']                   = eaf['sales_location']                                  # Field 80 (closest analog)
    dtrr['part_d_opt_out_flag']                      = yes_no_to_flag(eaf['part_d_opt_out'])                  # Field 63, Yes/No -> Y/N
    dtrr['premium_withhold_option']                  = eaf['premium_withhold_option']                         # Field 144
    dtrr['cumulative_uncovered_months']              = eaf['uncovered_months']                                # Field 77
    dtrr['creditable_coverage_flag']                 = yes_no_to_flag(eaf['creditable_coverage'])             # Field 76, Yes/No -> Y/N
    dtrr['employer_subsidy_override_flag']           = yes_no_to_flag(eaf['employer_subsidy_override'])       # Field 90, Yes/No -> Y/N
    dtrr['processing_timestamp']                     = None                                                   # System-generated
    dtrr['end_date']                                 = mmddyyyy_to_ccyymmdd(eaf['span_end_date'])             # Field 110, MMDDYYYY -> CCYYMMDD
    dtrr['submitted_uncovered_months']               = eaf['uncovered_months']                                # Field 77 (same source as above)
    dtrr['filler_189']                               = None
    dtrr['preferred_language_other_than_english']    = language_to_flag(eaf['language'])                      # Field 49, name/code -> S/O/X/space
    dtrr['accessible_format']                        = accessible_format_to_flag(eaf['accessibility_format']) # Field 174, word -> B/L/A/D/X
    dtrr['secondary_drug_insurance_flag']            = yes_no_to_flag(eaf['secondary_rx_flag'])               # Field 91, Yes/No -> Y/N
    dtrr['secondary_rx_id']                          = eaf['secondary_rx_id']                                 # Field 92
    dtrr['secondary_rx_group']                       = eaf['secondary_rx_group']                              # Field 93
    dtrr['eghp']                                     = yes_no_to_flag(eaf['eghp_flag'])                       # Field 88, Yes/No -> Y/N
    dtrr['part_d_lips_level']                        = eaf['lis_copay_level_id']                              # Field 61
    dtrr['low_income_copay_category']                = eaf['deemed_co_pay_level_id']                          # Field 62
    dtrr['low_income_period_effective_date']         = mmddyyyy_to_ccyymmdd(eaf['lis_effective_date'])        # Field 122, MMDDYYYY -> CCYYMMDD
    dtrr['part_d_lep_amount']                        = None                                                   # CMS-calculated
    dtrr['part_d_lep_waived_amount']                 = None                                                   # CMS-calculated
    dtrr['part_d_lep_subsidy_amount']                = None                                                   # CMS-calculated
    dtrr['low_income_part_d_premium_subsidy']        = eaf['subsidy_percentage']                              # Field 59
    dtrr['part_d_rx_bin']                            = eaf['rx_bin']                                          # Field 146
    dtrr['part_d_rx_pcn']                            = eaf['rx_pcn']                                          # Field 147
    dtrr['part_d_rx_group']                          = eaf['rx_group']                                        # Field 145
    dtrr['part_d_rx_id']                             = eaf['primary_rx_id']                                   # Field 121
    dtrr['secondary_rx_bin']                         = eaf['secondary_rx_bin']                                # Field 95
    dtrr['secondary_rx_pcn']                         = eaf['secondary_rx_pcn']                                # Field 148
    dtrr['de_minimis_differential_amount']           = None                                                   # CMS-calculated
    dtrr['msp_status_flag']                          = None                                                   # Not present on EAF
    dtrr['low_income_period_end_date']               = mmddyyyy_to_ccyymmdd(eaf['lis_term_date'])             # Field 123, MMDDYYYY -> CCYYMMDD
    dtrr['low_income_subsidy_source_code']           = eaf['deemed_reason_code']                              # Field 60
    dtrr['enrollee_type_flag_pbp_level']             = None                                                   # Not present on EAF
    dtrr['application_date_indicator']               = None                                                   # System-derived
    dtrr['trc_short_name']                           = None                                                   # CMS reply-side only
    dtrr['disenrollment_reason_code']                = eaf['disenrollment_reason']                            # Field 94
    dtrr['mmp_opt_out_flag']                         = eaf['mppp_action']                                     # Field 191 (closest analog, format unconfirmed)
    dtrr['cleanup_id']                               = None                                                   # CMS-internal
    dtrr['cara_status_add_update_delete_flag']       = None                                                   # Not present on EAF
    dtrr['pos_drug_edit_status']                     = None                                                   # Not present on EAF
    dtrr['drug_class']                               = None                                                   # Not present on EAF
    dtrr['pos_drug_edit_code']                       = None                                                   # Not present on EAF
    dtrr['cara_status_notification_start_date']      = None                                                   # Not present on EAF
    dtrr['cara_status_implementation_start_date']    = None                                                   # Not present on EAF
    dtrr['cara_status_notification_end_date']        = None                                                   # Not present on EAF
    dtrr['hospice_provider_number']                  = None                                                   # Not present on EAF
    dtrr['ic_model_type_indicator']                  = None                                                   # Not present on EAF
    dtrr['ic_model_end_date_reason_code']            = None                                                   # Not present on EAF
    dtrr['ic_model_benefit_status']                  = None                                                   # Not present on EAF
    dtrr['updated_medicaid_status_community_raf']    = eaf['medicaid_level']                                  # Field 166
    dtrr['cara_status_implementation_end_date']      = None                                                   # Not present on EAF
    dtrr['prescriber_limitation']                    = None                                                   # Not present on EAF
    dtrr['pharmacy_limitation']                      = None                                                   # Not present on EAF
    dtrr['filler_456']                               = None
    dtrr['system_assigned_transaction_tracking_id']  = eaf['unique_key']                                      # Field 106
    dtrr['plan_assigned_transaction_tracking_id']    = eaf['confirmation_number']                             # Field 1
    dtrr['relationship_agent']                       = relationship_flag(eaf['relationship_to_enrollee'], 1)  # Field 189 == 1
    dtrr['relationship_broker']                      = relationship_flag(eaf['relationship_to_enrollee'], 2)  # Field 189 == 2
    dtrr['relationship_ship_counselors']             = relationship_flag(eaf['relationship_to_enrollee'], 3)  # Field 189 == 3
    dtrr['relationship_authorized_reps']             = relationship_flag(eaf['relationship_to_enrollee'], 4)  # Field 189 == 4
    dtrr['relationship_other_third_parties']         = relationship_flag(eaf['relationship_to_enrollee'], 5)  # Field 189 == 5
    dtrr['relationship_self']                        = relationship_flag(eaf['relationship_to_enrollee'], 6)  # Field 189 == 6
    dtrr['relationship_form_left_blank']             = relationship_flag(eaf['relationship_to_enrollee'], 7)  # Field 189 == 7
    dtrr['national_producer_number']                 = eaf['national_producer_number']                        # Field 190
    dtrr['oec_indicator']                            = "Y" if str(eaf.get('application_type')) == "4" else "N"  # Field 143 == 4 (OEC/CMS)
    dtrr['oec_application_date']                     = mmddyyyy_to_ccyymmdd(eaf['submit_date'])               # Field 2, used when Field 143 == 4
    dtrr['oec_application_number']                   = eaf['confirmation_number']                             # Field 1, used as OEC App number
    dtrr['beneficiary_phone_number']                 = eaf['member_phone']                                    # Field 18
    dtrr['beneficiary_email_address']                = eaf['member_email_address']                            # Field 19

    return dtrr


if __name__ == "__main__":
    sample_eaf = {
        "mbi": "1EG4TE5MK73", "member_last_name": "SMITH", "member_first_name": "JOHN",
        "member_middle_initial": "Q", "member_gender": "M", "member_birth_date": "05151955",
        "contract_id": "H1234", "member_state": "CA", "esrd": "No", "transaction_type": "61",
        "effective_date": "01012026", "pbp_id": "001", "submit_date": "12152025",
        "sep_reason_code": "01", "sales_location": "12345", "application_sign_date": "12152025",
        "segment_id": "000", "election_type": "AEP", "part_d_opt_out": "No",
        "premium_withhold_option": "1", "uncovered_months": "0", "creditable_coverage": "Yes",
        "employer_subsidy_override": "No", "span_end_date": "", "language": "Spanish",
        "accessibility_format": "Remove", "secondary_rx_flag": "No", "secondary_rx_id": "",
        "secondary_rx_group": "", "eghp_flag": "No", "lis_copay_level_id": "1",
        "deemed_co_pay_level_id": "1", "lis_effective_date": "01012026", "subsidy_percentage": "100",
        "rx_bin": "610591", "rx_pcn": "PARTD", "rx_group": "RXGRP01", "primary_rx_id": "PRI12345678",
        "secondary_rx_bin": "", "secondary_rx_pcn": "", "lis_term_date": "12312026",
        "deemed_reason_code": "", "disenrollment_reason": "", "mppp_action": "",
        "medicaid_level": "", "unique_key": "PLANTXN-2026-000456", "confirmation_number": "APP20260212001",
        "relationship_to_enrollee": "6", "national_producer_number": "123456",
        "application_type": "4", "member_phone": "5551234567", "member_email_address": "john@example.com",
    }

    result = build_dtrr_record(sample_eaf)
    for k, v in result.items():
        print(f"  dtrr['{k}'] = {v!r}")
