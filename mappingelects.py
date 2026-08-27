cms_election_types = [
    {"mapping_code": "A", "audit_history_value": 1,  "abbreviation": "AEP",     "description": "Annual Election Period", "obsolete": False, "notes": None},
    {"mapping_code": "C", "audit_history_value": 17, "abbreviation": "SEPC",    "description": "Plan-submitted rollover enrollment transactions", "obsolete": False, "notes": None},
    {"mapping_code": "D", "audit_history_value": 15, "abbreviation": "MADP",    "description": "MA Disenrollment Period", "obsolete": True, "notes": "Obsolete as of January 1, 2019"},
    {"mapping_code": "E", "audit_history_value": 2,  "abbreviation": "IEP",     "description": "Initial Enrollment Period for Part D", "obsolete": False, "notes": None},
    {"mapping_code": "F", "audit_history_value": 14, "abbreviation": "IEP2",    "description": "Additional IEP for Part D", "obsolete": False, "notes": None},
    {"mapping_code": "I", "audit_history_value": 3,  "abbreviation": "ICEP",    "description": "Initial Coverage Election Period", "obsolete": False, "notes": None},
    {"mapping_code": "J", "audit_history_value": 18, "abbreviation": "SEPJ",    "description": "Default Enrollment Mechanism (DEM)", "obsolete": False, "notes": None},
    {"mapping_code": "L", "audit_history_value": 20, "abbreviation": "SEPL",    "description": "Dual/LIS Quarterly SEP", "obsolete": True, "notes": 'Obsolete for plan type "PDP" as of January 1, 2025'},
    {"mapping_code": "P", "audit_history_value": 21, "abbreviation": "SEPP",    "description": "Integrated Care SEP for D-SNP plans", "obsolete": False, "notes": None},
    {"mapping_code": "Q", "audit_history_value": 22, "abbreviation": "SEPQ",    "description": "DUAL/LIS MN SEP", "obsolete": False, "notes": "Applicable from January 1, 2025"},
    {"mapping_code": "M", "audit_history_value": 19, "abbreviation": "MAOEP",   "description": "Medicare Advantage - Open Enrollment Period", "obsolete": False, "notes": None},
    {"mapping_code": "N", "audit_history_value": 6,  "abbreviation": "OEPNEW",  "description": "Open Enrollment Period for Newly Eligible Individuals", "obsolete": True, "notes": "Obsolete as of December 31, 2010"},
    {"mapping_code": "O", "audit_history_value": 5,  "abbreviation": "OEP",     "description": "Open Enrollment Period", "obsolete": True, "notes": "Obsolete as of March 31, 2010; hidden from UI"},
    {"mapping_code": "R", "audit_history_value": 16, "abbreviation": "SEPR",    "description": "SEP for Enrollment into a 5-Star Plan", "obsolete": False, "notes": None},
    {"mapping_code": "S", "audit_history_value": 4,  "abbreviation": "SEPS",    "description": "Other SEP", "obsolete": False, "notes": None},
    {"mapping_code": "T", "audit_history_value": 7,  "abbreviation": "OEPI",    "description": "Open Enrollment Period for Institutionalized Individuals", "obsolete": False, "notes": None},
    {"mapping_code": "U", "audit_history_value": 8,  "abbreviation": "SEPU",    "description": "SEP for Gain/Loss/Change in Dual or LIS eligibility status", "obsolete": False, "notes": None},
    {"mapping_code": "V", "audit_history_value": 9,  "abbreviation": "SEPV",    "description": "SEP for Permanent Change in Residence", "obsolete": False, "notes": None},
    {"mapping_code": "W", "audit_history_value": 10, "abbreviation": "SEPW",    "description": "SEP EGHP (Employer/Union Group Health Plan)", "obsolete": False, "notes": None},
    {"mapping_code": "X", "audit_history_value": 11, "abbreviation": "SEPX",    "description": "SEP for Administrative Action", "obsolete": False, "notes": None},
    {"mapping_code": "Y", "audit_history_value": 12, "abbreviation": "SEPY",    "description": "SEP for CMS Casework Exceptional Conditions", "obsolete": False, "notes": None},
    {"mapping_code": "Z", "audit_history_value": 13, "abbreviation": "SEPZ",    "description": "CMS-only Special Election Period for Auto/Facilitated Enrollments", "obsolete": False, "notes": "SEPZ is EAM's name for what CMS calls CEP"},
]

# Convenience lookup dicts
election_type_by_code = {row["mapping_code"]: row for row in cms_election_types}
election_type_by_abbreviation = {row["abbreviation"]: row for row in cms_election_types}
election_type_code_to_abbreviation = {row["mapping_code"]: row["abbreviation"] for row in cms_election_types}
active_election_types = [row for row in cms_election_types if not row["obsolete"]]


# ---------------------------------------------------------------------------
# 2. SEP REASON CODES MAPPING  (EAM Appendices Guide 6.10, p.13-17)
# ---------------------------------------------------------------------------

sep_reason_codes = [
    {"reason_code": "00*", "election_type": None,   "description": "CMS-Initiated Enrollment/Disenrollment", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": None,      "obsolete": False, "notes": None},
    {"reason_code": "01",  "election_type": "SEPS",  "description": "GOVT EMERGENCY OR DISASTER", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "DST",     "obsolete": False, "notes": None},
    {"reason_code": "02",  "election_type": "SEPS",  "description": "GOVT EMERG/DISASTER-COVID19", "ma_ma_pd": False, "pdp": False, "oec_sep_reason": None,      "obsolete": True,  "notes": "Deactivated by CMS effective 11/30/2021"},
    {"reason_code": "11",  "election_type": "SEPS",  "description": "CMS TERM OF CONTRACT", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "MYT",     "obsolete": False, "notes": None},
    {"reason_code": "12",  "election_type": "SEPS",  "description": "TERM/CNTRCT MOD MUTUAL CONSENT", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "EOC",     "obsolete": False, "notes": None},
    {"reason_code": "21",  "election_type": "SEPS",  "description": "ACCESSIBLE FRMT RECEIPT DELAY", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "ACC",     "obsolete": False, "notes": None},
    {"reason_code": "22",  "election_type": "SEPS",  "description": "INVOL LOSS OF CRED CVG", "ma_ma_pd": "61 only", "pdp": True, "oec_sep_reason": "LCC",     "obsolete": False, "notes": None},
    {"reason_code": "23",  "election_type": "SEPS",  "description": "DISENROLL DUE TO CMS SANCTION", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "SAN",     "obsolete": False, "notes": None},
    {"reason_code": "24",  "election_type": "SEPS",  "description": "PART D DISENR FOR OTH CRED CVG", "ma_ma_pd": "61 only", "pdp": False, "oec_sep_reason": None,   "obsolete": False, "notes": None},
    {"reason_code": "25",  "election_type": "SEPS",  "description": "INVOL DISENROLL LOSS OF PART B", "ma_ma_pd": False, "pdp": True,  "oec_sep_reason": "INV",     "obsolete": False, "notes": None},
    {"reason_code": "26",  "election_type": "OEPI",  "description": "MA OEPI DISENROLL FROM MA", "ma_ma_pd": False, "pdp": True,  "oec_sep_reason": "IIP",     "obsolete": False, "notes": None},
    {"reason_code": "27",  "election_type": "SEPS",  "description": "PACE", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "PAC",     "obsolete": False, "notes": None},
    {"reason_code": "28",  "election_type": "SEPS",  "description": "COST PLANS NON-RENEWALS", "ma_ma_pd": "61 only", "pdp": True, "oec_sep_reason": None,      "obsolete": False, "notes": None},
    {"reason_code": "29",  "election_type": "SEPS",  "description": "DROP MEDIGAP IN TRIAL PERIOD", "ma_ma_pd": False, "pdp": True,  "oec_sep_reason": "12G",     "obsolete": False, "notes": None},
    {"reason_code": "30",  "election_type": "SEPS",  "description": "CHRONIC CARE C-SNP", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "CSN",     "obsolete": False, "notes": None},
    {"reason_code": "31",  "election_type": "SEPS",  "description": "INSTITUTIONAL INDIVIDUAL", "ma_ma_pd": False, "pdp": True,  "oec_sep_reason": "IND",     "obsolete": False, "notes": None},
    {"reason_code": "32",  "election_type": "SEPS",  "description": "RETRO ENTITLEMENT DETERM", "ma_ma_pd": "61 only", "pdp": True, "oec_sep_reason": "RET",     "obsolete": False, "notes": None},
    {"reason_code": "33",  "election_type": "SEPS",  "description": "BENES AGE 65 (SEP65)", "ma_ma_pd": False, "pdp": True,  "oec_sep_reason": "12J",     "obsolete": False, "notes": None},
    {"reason_code": "34",  "election_type": "SEPS",  "description": "PART B GEP ENROLLMENT", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "PRE",     "obsolete": False, "notes": None},
    {"reason_code": "35",  "election_type": "SEPS",  "description": "LOSS OF SNP", "ma_ma_pd": "61 only", "pdp": True, "oec_sep_reason": "SNP",     "obsolete": False, "notes": None},
    {"reason_code": "36",  "election_type": "SEPS",  "description": "COST DISENRL OR OPT SUP PART D", "ma_ma_pd": False, "pdp": True,  "oec_sep_reason": "OSD",     "obsolete": False, "notes": None},
    {"reason_code": "37",  "election_type": "SEPS",  "description": "LAWFULLY PRESENT", "ma_ma_pd": "61 only", "pdp": True, "oec_sep_reason": "LAW",     "obsolete": False, "notes": None},
    {"reason_code": "38",  "election_type": "SEPS",  "description": "QUALIFIED / LOSE SPAP ELIG", "ma_ma_pd": "61 only", "pdp": True, "oec_sep_reason": "PAP",     "obsolete": False, "notes": None},
    {"reason_code": "39",  "election_type": "SEPS",  "description": "PLAN IN RECEIVERSHIP", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "REC",     "obsolete": False, "notes": None},
    {"reason_code": "40",  "election_type": "SEPS",  "description": "CMS ID CONSISTENT POOR PERF", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "LPI",     "obsolete": False, "notes": None},
    {"reason_code": "41",  "election_type": "SEPS",  "description": "MA ADD PART D IEP", "ma_ma_pd": "X1 (MA only plan)", "pdp": True, "oec_sep_reason": None,  "obsolete": False, "notes": None},
    {"reason_code": "42",  "election_type": "SEPS",  "description": "MA for A/B Except Cond Enroll", "ma_ma_pd": "61 only", "pdp": False, "oec_sep_reason": "CSP",   "obsolete": False, "notes": None},
    {"reason_code": "43",  "election_type": "SEPS",  "description": "PT D- A/B Except Cond Enroll", "ma_ma_pd": "61 only", "pdp": True, "oec_sep_reason": "DSP",    "obsolete": False, "notes": None},
    {"reason_code": "90",  "election_type": "SEPS",  "description": "MISINFORM CREDITABLE STATUS", "ma_ma_pd": "61 only", "pdp": True, "oec_sep_reason": "OTH/CRE", "obsolete": False, "notes": None},
    {"reason_code": "91",  "election_type": "SEPS",  "description": "PROVIDER NETWORK", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "OTH/PRO", "obsolete": False, "notes": None},
    {"reason_code": "92",  "election_type": "SEPS",  "description": "CONTRACT VIOLATION", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "OTH/VIO", "obsolete": False, "notes": None},
    {"reason_code": "93",  "election_type": "SEPS",  "description": "OTHER EXCEPTIONAL CIRCUMSTANCES", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": "OTH",     "obsolete": False, "notes": None},
    {"reason_code": "94",  "election_type": "SEPS",  "description": "INSULIN SEP", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": None,      "obsolete": True,  "notes": "Obsolete as of release 6.00.003.005; deactivated by CMS effective 1/1/2024; still visible on historical transactions in View/Edit Member UI"},
    {"reason_code": "95",  "election_type": None,    "description": "PLAN LIST CORRECTION SEP", "ma_ma_pd": False, "pdp": False, "oec_sep_reason": None,  "obsolete": True,  "notes": "Obsolete as of release 6.00.002.001; visible on historical transactions in View/Edit Transaction UI only, not View/Edit Member UI"},
    {"reason_code": "96",  "election_type": None,    "description": "OTHER EXC CIRC-MARKET MISREP", "ma_ma_pd": "61 only", "pdp": True, "oec_sep_reason": "EXC",   "obsolete": False, "notes": None},
    {"reason_code": "Y1",  "election_type": "SEPY",  "description": "EXCEPTIONAL CIRCUMSTANCE", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": None,      "obsolete": False, "notes": None},
    {"reason_code": "Y2",  "election_type": "SEPY",  "description": None, "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": None,      "obsolete": False, "notes": None},
    {"reason_code": "Y3",  "election_type": "SEPY",  "description": None, "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": None,      "obsolete": False, "notes": None},
    {"reason_code": "Y4",  "election_type": "SEPY",  "description": None, "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": None,      "obsolete": False, "notes": None},
    {"reason_code": "Y5",  "election_type": None,    "description": "EXCEP CIRC-MARKET MISREP", "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": None,      "obsolete": False, "notes": None},
    {"reason_code": "YA",  "election_type": "SEPY",  "description": None, "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": None,      "obsolete": False, "notes": None},
    {"reason_code": "YB",  "election_type": "SEPY",  "description": None, "ma_ma_pd": True,  "pdp": True,  "oec_sep_reason": None,      "obsolete": False, "notes": None},
]