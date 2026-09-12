"""
DTRR (Daily Transaction Reply Report) Detail Record - field/column names,
in record order (Item 1-102, with lettered conditional sub-fields for
Item 24 [pos 85-96, content depends on the TRC] and Item 95 [Relationship
to enrollee sub-flags]).

This is the single fixed-width (800-byte) reply record MARx returns for
every submitted transaction, including TC 61 (new enrollment / PBP change).
Fields flagged tc61_specific in dtrr_tc61_field_validation.py are those the
guide calls out as populated specifically for TC 61 (e.g., Prior PBP ID,
Preferred Language, Accessible Format, Secondary Drug Insurance Flag, EGHP,
Part D/Secondary Rx BIN-PCN-Group-ID, Relationship to enrollee).
"""

columns = [
    'Beneficiary ID',  # item 1
    'Surname',  # item 2
    'First Name',  # item 3
    'Middle Initial',  # item 4
    'Sex Code',  # item 5
    'Date of Birth',  # item 6
    'Record Type',  # item 7
    'Contract Number',  # item 8
    'State Code',  # item 9
    'County Code',  # item 10
    'Disability Indicator',  # item 11
    'Hospice Indicator',  # item 12
    'Institutional/NHC/HCBS Indicator',  # item 13
    'ESRD Indicator',  # item 14
    'Transaction Reply Code',  # item 15
    'Transaction Code',  # item 16
    'Entitlement Type Code',  # item 17
    'Effective Date',  # item 18
    'WA Indicator',  # item 19
    'Plan Benefit Package ID',  # item 20
    'Filler',  # item 21
    'Transaction Date',  # item 22
    'UI Initiated Change Flag',  # item 23
    'Effective Date of the Disenrollment',  # item 24a
    'New Enrollment Effective Date',  # item 24b
    'Claim Number (old)',  # item 24c
    'Date of Death',  # item 24d
    'Hospice End Date',  # item 24e
    'ESRD Start Date',  # item 24f
    'ESRD End Date',  # item 24g
    'Institutional/ NHC Start Date',  # item 24h
    'Medicaid Start Date',  # item 24i
    'Medicaid End Date',  # item 24j
    'Part A End Date',  # item 24k
    'WA Start Date',  # item 24l
    'WA End Date',  # item 24m
    'Part A Reinstate Date',  # item 24n
    'Part B End Date',  # item 24o
    'Part B Reinstate Date',  # item 24p
    'Old State and County Codes',  # item 24q
    'Attempted Enroll Effective Date',  # item 24r
    'PBP Effective Date',  # item 24s
    'Correct Part D Premium Rate',  # item 24t
    'Date Identifying Information Changed by UI User',  # item 24u
    'Modified Part C Premium Amount',  # item 24v
    'Date of Death Removed',  # item 24w
    'Dialysis End Date',  # item 24x
    'Transplant Failure Date',  # item 24y
    'New ZIP Code',  # item 24z
    'Previous Contract for POS Drug Edit or CARA Status Active Indicator',  # item 24aa
    'MSP Period Start Date',  # item 24bb
    'Maximum NUNCMO Calculated',  # item 24cc
    'IC Model End Date',  # item 24dd
    'Residence Address End Date',  # item 24ee
    'Withholding Agency Rejection Code',  # item 24ff
    'MPPP Termination Reason Code',  # item 24gg
    'District Office Code',  # item 25
    'Previous Part D Contract/PBP for TrOOP Transfer.',  # item 26
    'SEP Reason Code',  # item 27
    'Filler',  # item 28
    'Source ID',  # item 29
    'Prior Plan Benefit Package ID',  # item 30
    'Application Date',  # item 31
    'UI User Organization Designation',  # item 32
    'Out of Area Flag',  # item 33
    'Segment Number',  # item 34
    'Part C Beneficiary Premium',  # item 35
    'Part D Beneficiary Premium',  # item 36
    'Election Type Code',  # item 37
    'Enrollment Source Code',  # item 38
    'Part D Opt-Out Flag',  # item 39
    'Premium Withhold Option/Parts C-D',  # item 40
    'Cumulative Number of Uncovered Months',  # item 41
    'Creditable Coverage Flag',  # item 42
    'Employer Subsidy Override Flag',  # item 43
    'Processing Timestamp',  # item 44
    'End Date',  # item 45
    'Submitted Number of Uncovered Months',  # item 46
    'Filler',  # item 47
    'Preferred Language Other Than English',  # item 48
    'Accessible Format',  # item 49
    'Secondary Drug Insurance Flag',  # item 50
    'Secondary Rx ID',  # item 51
    'Secondary Rx Group',  # item 52
    'EGHP',  # item 53
    'Part D Low-Income Premium Subsidy Level',  # item 54
    'Low-Income Co-Pay Category',  # item 55
    'Low-Income Period Effective Date',  # item 56
    'Part D Late Enrollment Penalty Amount',  # item 57
    'Part D Late Enrollment Penalty Waived Amount',  # item 58
    'Part D Late Enrollment Penalty Subsidy Amount',  # item 59
    'Low-Income Part D Premium Subsidy Amount',  # item 60
    'Part D Rx BIN',  # item 61
    'Part D Rx PCN',  # item 62
    'Part D Rx Group',  # item 63
    'Part D Rx ID',  # item 64
    'Secondary Rx BIN',  # item 65
    'Secondary Rx PCN',  # item 66
    'De Minimis Differential Amount',  # item 67
    'MSP Status Flag',  # item 68
    'Low Income Period End Date',  # item 69
    'Low Income Subsidy Source Code',  # item 70
    'Enrollee Type Flag, PBP Level',  # item 71
    'Application Date Indicator',  # item 72
    'TRC Short Name',  # item 73
    'Disenrollment Reason Code',  # item 74
    'MMP Opt Out Flag',  # item 75
    'Cleanup ID',  # item 76
    'CARA Status Add/Update/Delete Flag',  # item 77
    'POS Drug Edit Status',  # item 78
    'Drug Class',  # item 79
    'POS Drug Edit Code',  # item 80
    'CARA Status Notification Start Date',  # item 81
    'CARA Status Implementation Start Date',  # item 82
    'CARA Status Notification End Date',  # item 83
    'Hospice Provider Number',  # item 84
    'IC Model Type Indicator',  # item 85
    'IC Model End Date Reason Code',  # item 86
    'IC Model Benefit Status',  # item 87
    'Updated Medicaid Status for Community RAF beneficiary',  # item 88
    'CARA Status Implementation End Date',  # item 89
    'Prescriber Limitation',  # item 90
    'Pharmacy Limitation',  # item 91
    'Filler',  # item 92
    'System Assigned Transaction Tracking ID',  # item 93
    'Plan Assigned Transaction Tracking ID',  # item 94
    'Relationship to enrollee',  # item 95
    'Agent',  # item 95a
    'Broker',  # item 95b
    'SHIP counselors',  # item 95c
    'Authorized representatives',  # item 95d
    'Other (third parties)',  # item 95e
    'Self',  # item 95f
    'Form left blank',  # item 95g
    'National Producer Number (NPN)',  # item 96
    'OEC Indicator',  # item 97
    'OEC Application Date',  # item 98
    'OEC Application Number',  # item 99
    'Beneficiary Phone Number',  # item 100
    'Beneficiary Email Address',  # item 101
    'Filler',  # item 102
]
