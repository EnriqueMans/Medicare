"""
eaf_converter.py
=================
Converts tabular member/enrollment data (e.g., a list of dicts, a CSV, or a
pandas DataFrame) into a TriZetto Enrollment Administration Manager (EAM)
EAF file — the 222-field tab-delimited layout described in the
"EAM EAF Layout Guide v26" (Feb 2026, rev. May 2026).

Format rules implemented, per the guide:
  - Tab-delimited text file, first row = column headers (field names).
  - All date fields must be MMDDYYYY; if missing, EAM defaults to 01011900,
    so this script fills any blank *Date field with that default.
  - Only ASCII printable characters are allowed; non-ASCII/control chars are
    stripped from every value.
  - For non-transactional updates, callers should only pass the fields that
    are actually changing (leave the rest blank in the row dict).
  - Max file name length for the EAF itself is 75 characters (checked at
    write time).

Usage:
    from eaf_converter import write_eaf, EAF_FIELDS

    rows = [
        {"ConfirmationNumber": "ABC244654345", "ContractID": "H0001",
         "PBPID": "001", "MemberFirstName": "John", "MemberLastName": "Smith",
         "MemberBirthDate": "07131936", "TransactionType": "61"},
    ]
    write_eaf(rows, "outbound/H0001_20260704.txt")
"""

import csv
import os
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# 222-field layout (auto-extracted from the EAM EAF Layout Guide v26).
# "name" is the column header written to the file. Fields whose name ends
# in an asterisk in the guide (e.g., MemberFirstName*) are flagged there as
# updatable via TC 00; the asterisk itself is not part of the file header.
# ---------------------------------------------------------------------------
EAF_FIELDS = [
    {"num": 1, "name": 'ConfirmationNumber', "max_len": '32', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 2, "name": 'SubmitDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 3, "name": 'ContractID', "max_len": '5', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 4, "name": 'PBPID', "max_len": '3', "type": 'Numeric', "tc00_updatable": False},
    {"num": 5, "name": 'SegmentID', "max_len": '3', "type": 'Numeric', "tc00_updatable": False},
    {"num": 6, "name": 'MemberTitle', "max_len": '5', "type": 'Alpha', "tc00_updatable": True},
    {"num": 7, "name": 'MemberFirstName', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 8, "name": 'MemberMiddleInitial', "max_len": '1', "type": 'Alpha', "tc00_updatable": True},
    {"num": 9, "name": 'MemberLastName', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 10, "name": 'MemberBirthDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 11, "name": 'MemberGender', "max_len": '1', "type": 'Alpha', "tc00_updatable": True},
    {"num": 12, "name": 'MemberAddress1', "max_len": '35', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 13, "name": 'MemberAddress2', "max_len": '18', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 14, "name": 'MemberAddress3', "max_len": '17', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 15, "name": 'MemberCity', "max_len": '50', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 16, "name": 'MemberState', "max_len": '2', "type": 'Alpha', "tc00_updatable": True},
    {"num": 17, "name": 'MemberZip', "max_len": '10', "type": 'Numeric', "tc00_updatable": True},
    {"num": 18, "name": 'MemberPhone', "max_len": '10', "type": 'Numeric', "tc00_updatable": False},
    {"num": 19, "name": 'MemberEmailAddress', "max_len": '128', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 20, "name": 'MemberMBI', "max_len": '15', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 21, "name": 'ApplicationSSN', "max_len": '11', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 22, "name": 'MailingAddress1', "max_len": '35', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 23, "name": 'MailingAddress2', "max_len": '18', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 24, "name": 'MailingAddress3', "max_len": '17', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 25, "name": 'MailingCity', "max_len": '50', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 26, "name": 'MailingState', "max_len": '2', "type": 'Alpha', "tc00_updatable": True},
    {"num": 27, "name": 'MailingZip', "max_len": '10', "type": 'Numeric', "tc00_updatable": True},
    {"num": 28, "name": 'MedicarePartA', "max_len": '8', "type": 'Numeric', "tc00_updatable": True},
    {"num": 29, "name": 'MedicarePartB', "max_len": '8', "type": 'Numeric', "tc00_updatable": True},
    {"num": 30, "name": 'EmergencyContact', "max_len": '25', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 31, "name": 'EmergencyPhone', "max_len": '10', "type": 'Numeric', "tc00_updatable": True},
    {"num": 32, "name": 'EmergencyRelationship', "max_len": '16', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 33, "name": 'PremiumDeducted_Retired', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 34, "name": 'PremiumSource_Retired', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 35, "name": 'OtherCoverage', "max_len": '3', "type": 'Alpha', "tc00_updatable": True},
    {"num": 36, "name": 'OtherCoverageName', "max_len": '30', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 37, "name": 'OtherCoverageID', "max_len": '16', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 38, "name": 'LongTerm', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 39, "name": 'LongTermName', "max_len": '30', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 40, "name": 'LongTermAddress', "max_len": '255', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 41, "name": 'LongTermPhone', "max_len": '10', "type": 'Numeric', "tc00_updatable": False},
    {"num": 42, "name": 'AuthorizedRepName', "max_len": '30', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 43, "name": 'AuthorizedRepAddress', "max_len": '255', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 44, "name": 'AuthorizedRepCity', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 45, "name": 'AuthorizedRepState', "max_len": '2', "type": 'Alpha', "tc00_updatable": True},
    {"num": 46, "name": 'AuthorizedRepZip', "max_len": '10', "type": 'Numeric', "tc00_updatable": True},
    {"num": 47, "name": 'AuthorizedRepPhone', "max_len": '10', "type": 'Numeric', "tc00_updatable": False},
    {"num": 48, "name": 'AuthorizedRepRelationship', "max_len": '32', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 49, "name": 'Language', "max_len": '30', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 50, "name": 'ESRD', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 51, "name": 'StateMedicaid', "max_len": '3', "type": 'Alpha', "tc00_updatable": True},
    {"num": 52, "name": 'WorkStatus', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 53, "name": 'PrimaryCarePhysician_Retired', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 54, "name": 'OtherCoverageGroup', "max_len": '32', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 55, "name": 'AgentID', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 56, "name": 'SubmitTime', "max_len": '23', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 57, "name": 'PartDSubAppInd', "max_len": '1', "type": 'Alpha', "tc00_updatable": False},
    {"num": 58, "name": 'DeemedInd', "max_len": '1', "type": 'Alpha', "tc00_updatable": False},
    {"num": 59, "name": 'SubsidyPercentage', "max_len": '3', "type": 'Numeric', "tc00_updatable": False},
    {"num": 60, "name": 'DeemedReasonCode', "max_len": '3', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 61, "name": 'LISCopayLevelID', "max_len": '1', "type": 'Numeric', "tc00_updatable": False},
    {"num": 62, "name": 'DeemedCopayLevelID', "max_len": '1', "type": 'Numeric', "tc00_updatable": False},
    {"num": 63, "name": 'PartDOptOut', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 64, "name": 'SEPReasonCode', "max_len": '12', "type": 'Alpha', "tc00_updatable": False},
    {"num": 65, "name": 'SEPCMSReason', "max_len": '32', "type": 'Alpha', "tc00_updatable": False},
    {"num": 66, "name": 'PremiumDirectPay_Retired', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 67, "name": 'EnrollmentPlanYear', "max_len": '4', "type": 'Numeric', "tc00_updatable": False},
    {"num": 68, "name": 'MemberID', "max_len": '15', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 69, "name": 'GroupNumber', "max_len": '8', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 70, "name": 'SubGroupNumber', "max_len": '4', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 71, "name": 'ClassNumber', "max_len": '4', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 72, "name": 'BillingProfileID', "max_len": '32', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 73, "name": 'EffectiveDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 74, "name": 'TransactionType', "max_len": '2', "type": 'Numeric', "tc00_updatable": False},
    {"num": 75, "name": 'ApplicationSignDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 76, "name": 'CreditableCoverage', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 77, "name": 'UncoveredMonths', "max_len": '3', "type": 'Numeric', "tc00_updatable": False},
    {"num": 78, "name": 'ElectionType', "max_len": '6', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 79, "name": 'MedicaidNumber', "max_len": '15', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 80, "name": 'SalesLocation', "max_len": '255', "type": 'Text', "tc00_updatable": False},
    {"num": 81, "name": 'BankAccountType', "max_len": '1', "type": 'Numeric', "tc00_updatable": False},
    {"num": 82, "name": 'BankAccountNumber', "max_len": '20', "type": 'Numeric', "tc00_updatable": False},
    {"num": 83, "name": 'BankACHRouting', "max_len": '9', "type": 'Numeric', "tc00_updatable": False},
    {"num": 84, "name": 'MedicalProduct', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 85, "name": 'PharmacyProduct', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 86, "name": 'VisionProduct', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 87, "name": 'DentalProduct', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 88, "name": 'EGHPFlag', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 89, "name": 'PriorCommercial', "max_len": '1', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 90, "name": 'EmployerSubsidy', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 91, "name": 'SecondaryRxFlag', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 92, "name": 'SecondaryRxID', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 93, "name": 'SecondaryRxGroup', "max_len": '15', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 94, "name": 'DisenrollmentReason', "max_len": '2', "type": 'Numeric', "tc00_updatable": False},
    {"num": 95, "name": 'SecondaryRxBIN', "max_len": '6', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 96, "name": 'Plan1', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": True},
    {"num": 97, "name": 'Plan2', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": True},
    {"num": 98, "name": 'Plan3', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": True},
    {"num": 99, "name": 'Plan4', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": True},
    {"num": 100, "name": 'Plan5', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": True},
    {"num": 101, "name": 'Plan6', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": True},
    {"num": 102, "name": 'Plan7', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": True},
    {"num": 103, "name": 'Plan8', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": True},
    {"num": 104, "name": 'Plan9', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": True},
    {"num": 105, "name": 'Plan10', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": True},
    {"num": 106, "name": 'UniqueKey', "max_len": '30', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 107, "name": 'SpanType', "max_len": '5', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 108, "name": 'SpanValue', "max_len": '15', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 109, "name": 'SpanStartDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 110, "name": 'SpanEndDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 111, "name": 'Trans-LevelPlan1', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": False},
    {"num": 112, "name": 'Trans-LevelPlan2', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": False},
    {"num": 113, "name": 'Trans-LevelPlan3', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": False},
    {"num": 114, "name": 'Trans-LevelPlan4', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": False},
    {"num": 115, "name": 'Trans-LevelPlan5', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": False},
    {"num": 116, "name": 'Trans-LevelPlan6', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": False},
    {"num": 117, "name": 'Trans-LevelPlan7', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": False},
    {"num": 118, "name": 'Trans-LevelPlan8', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": False},
    {"num": 119, "name": 'Trans-LevelPlan9', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": False},
    {"num": 120, "name": 'Trans-LevelPlan10', "max_len": '20', "type": 'Plan-defined', "tc00_updatable": False},
    {"num": 121, "name": 'PrimaryRxID', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 122, "name": 'LISEffectiveDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 123, "name": 'LISTermDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 124, "name": 'SCCCode', "max_len": '5', "type": 'Numeric', "tc00_updatable": False},
    {"num": 125, "name": 'NewtoMedicare', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 126, "name": 'Recentlymoved', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 127, "name": 'Recentlyreturnedto', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 128, "name": 'Extrahelpfor', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 129, "name": 'ExtrahelpforDrug', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 130, "name": 'Nomorehelpfor', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 131, "name": 'LongTermCare', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 132, "name": 'LeftPACEprogram', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 133, "name": 'Lostdrugcoverage', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 134, "name": 'Leavingemployeror', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 135, "name": 'Pharmacyassistance', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 136, "name": 'Planendingcontract', "max_len": '3', "type": 'Alpha', "tc00_updatable": False},
    {"num": 137, "name": 'DisenrolledfromSNP', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 138, "name": 'RecentlyChanged', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 139, "name": 'LeftMAPlan', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 140, "name": 'PCPID', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 141, "name": 'IPAGroupID', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 142, "name": 'SEPSReason', "max_len": '2', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 143, "name": 'ApplicationType', "max_len": '2', "type": 'Numeric', "tc00_updatable": False},
    {"num": 144, "name": 'PremiumWithhold', "max_len": '1', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 145, "name": 'RxGroup', "max_len": '15', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 146, "name": 'RxBIN', "max_len": '6', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 147, "name": 'RxPCN', "max_len": '10', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 148, "name": 'SecondaryRxPCN', "max_len": '10', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 149, "name": 'SalesDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 150, "name": 'EmployerGroup', "max_len": '15', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 151, "name": 'MedicarePartD', "max_len": '8', "type": 'Numeric', "tc00_updatable": True},
    {"num": 152, "name": 'SecondPhone', "max_len": '10', "type": 'Numeric', "tc00_updatable": False},
    {"num": 153, "name": 'PCPLastName', "max_len": '100', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 154, "name": 'PCPFirstName', "max_len": '100', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 155, "name": 'PCPEffDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 156, "name": 'PCPEndDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 157, "name": 'PCPProviderID', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 158, "name": 'Releasedfrom', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 159, "name": 'LawfulPresenceinUS', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 160, "name": 'RFIReceiptDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 161, "name": 'MedicalOSB', "max_len": '15', "type": 'AlphaNumeric', "tc00_updatable": False},
    {"num": 162, "name": 'DentalOSB', "max_len": '15', "type": 'AlphaNumeric', "tc00_updatable": False},
    {"num": 163, "name": 'VisionOSB', "max_len": '15', "type": 'AlphaNumeric', "tc00_updatable": False},
    {"num": 164, "name": 'OtherOSB', "max_len": '240', "type": 'AlphaNumeric', "tc00_updatable": False},
    {"num": 165, "name": 'On-HoldStatus', "max_len": '4', "type": 'Numeric', "tc00_updatable": False},
    {"num": 166, "name": 'MedicaidLevel', "max_len": '50', "type": 'Alphaumeric', "tc00_updatable": True},
    {"num": 167, "name": 'OnHoldReason', "max_len": '250', "type": 'Alpha', "tc00_updatable": False},
    {"num": 168, "name": 'IsMAOEP', "max_len": '1', "type": 'Alpha', "tc00_updatable": False},
    {"num": 169, "name": 'EnrollMedicareDate', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 170, "name": 'IsEmergency', "max_len": '1', "type": 'Alpha', "tc00_updatable": False},
    {"num": 171, "name": 'DupeEditOvr', "max_len": '3', "type": 'Varchar', "tc00_updatable": False},
    {"num": 172, "name": 'DateEditOvr', "max_len": '3', "type": 'Varchar', "tc00_updatable": False},
    {"num": 173, "name": 'SpouseWorkStatus', "max_len": '3', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 174, "name": 'AccessibilityFormat', "max_len": '10', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 175, "name": 'EmailOptIn', "max_len": '3', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 176, "name": 'Race', "max_len": '0', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 177, "name": 'Ethnicity', "max_len": '0', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 178, "name": 'PreferredFirstName', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 179, "name": 'PreferredLastName', "max_len": '20', "type": 'Alphanumeric', "tc00_updatable": True},
    {"num": 180, "name": 'PreferredPronoun', "max_len": '0', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 181, "name": 'GenderIdentity', "max_len": '0', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 182, "name": 'Non-BinaryGender', "max_len": '1', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 183, "name": 'MemberAddress', "max_len": '8', "type": 'Numeric', "tc00_updatable": False},
    {"num": 184, "name": 'MailingCountryCode', "max_len": '2', "type": 'Alpha', "tc00_updatable": False},
    {"num": 185, "name": 'DifferentGender', "max_len": '25', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 186, "name": 'Self-Identify', "max_len": '1', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 187, "name": 'DifferentSelf-Identify', "max_len": '25', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 188, "name": 'IndividualRepName', "max_len": '100', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 189, "name": 'Relationshipto', "max_len": '1', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 190, "name": 'NationalProducer', "max_len": '10', "type": 'Numeric', "tc00_updatable": False},
    {"num": 191, "name": 'MPPPAction', "max_len": '1', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 192, "name": 'MPPPTermination', "max_len": '2', "type": 'Alphanumeric', "tc00_updatable": False},
    {"num": 193, "name": 'MPPPTerminationDate', "max_len": '8', "type": 'Date', "tc00_updatable": False},
    {"num": 194, "name": 'ReservedForFutureUse_12', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 195, "name": 'ReservedForFutureUse_13', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 196, "name": 'ReservedForFutureUse_14', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 197, "name": 'ReservedForFutureUse_15', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 198, "name": 'ReservedForFutureUse_16', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 199, "name": 'ReservedForFutureUse_17', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 200, "name": 'ReservedForFutureUse_18', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 201, "name": 'ReservedForFutureUse_19', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 202, "name": 'ReservedForFutureUse_20', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 203, "name": 'ReservedForFutureUse_21', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 204, "name": 'ReservedForFutureUse_22', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 205, "name": 'ReservedForFutureUse_23', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 206, "name": 'ReservedForFutureUse_24', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 207, "name": 'ReservedForFutureUse_25', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 208, "name": 'ReservedForFutureUse_26', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 209, "name": 'ReservedForFutureUse_27', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 210, "name": 'ReservedForFutureUse_28', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 211, "name": 'ReservedForFutureUse_29', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 212, "name": 'ReservedForFutureUse_30', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 213, "name": 'ReservedForFutureUse_31', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 214, "name": 'ReservedForFutureUse_32', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 215, "name": 'ReservedForFutureUse_33', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 216, "name": 'ReservedForFutureUse_34', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 217, "name": 'ReservedForFutureUse_35', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 218, "name": 'ReservedForFutureUse_36', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 219, "name": 'ReservedForFutureUse_37', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 220, "name": 'ReservedForFutureUse_38', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 221, "name": 'ReservedForFutureUse_39', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
    {"num": 222, "name": 'ReservedForFutureUse_40', "max_len": '0', "type": 'N/A', "tc00_updatable": False},
]

HEADER_ROW = [f["name"] for f in EAF_FIELDS]
DATE_FIELD_NAMES = {f["name"] for f in EAF_FIELDS if "Date" in f["name"]}
DEFAULT_DATE = "01011900"

_ASCII_PRINTABLE_RE = re.compile(r"[^\x20-\x7E]")


def _clean_value(field_name, value):
    """Apply EAF formatting rules to a single field value."""
    if value is None:
        value = ""
    value = str(value)

    # Strip anything that is not an ASCII printable character.
    value = _ASCII_PRINTABLE_RE.sub("", value)

    # Tabs/newlines would corrupt the tab-delimited layout.
    value = value.replace("\t", " ").replace("\r", " ").replace("\n", " ")

    # Date fields default to 01011900 when not supplied.
    if field_name in DATE_FIELD_NAMES and not value.strip():
        value = DEFAULT_DATE

    return value


def build_row(record):
    """Build one EAF data row (list of str) from a dict keyed by field name.

    Any field not present in `record` is written as an empty string, except
    date fields, which default to 01011900 per the EAM EAF Layout Guide.
    Unrecognized keys in `record` are ignored.
    """
    return [_clean_value(name, record.get(name, "")) for name in HEADER_ROW]


def rows_from_csv(csv_path, encoding="utf-8"):
    """Read a source CSV (headers = EAF field names, any subset/order) and
    return a list of dicts ready for `write_eaf`."""
    with open(csv_path, newline="", encoding=encoding) as f:
        return list(csv.DictReader(f))


def rows_from_dataframe(df):
    """Convert a pandas DataFrame (columns = EAF field names) to row dicts."""
    return df.to_dict(orient="records")


def write_eaf(records, output_path, encoding="utf-8"):
    """Write `records` (an iterable of dicts keyed by EAF field name) to a
    tab-delimited EAF file at `output_path`.

    Raises ValueError if the output file name exceeds the 75-character
    limit documented in the EAM EAF Layout Guide.
    """
    filename = os.path.basename(output_path)
    if len(filename) > 75:
        raise ValueError(
            f"EAF file name '{filename}' is {len(filename)} characters; "
            f"the EAM EAF Layout Guide limits file names to 75 characters."
        )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(HEADER_ROW)
        for record in records:
            writer.writerow(build_row(record))

    return output_path


if __name__ == "__main__":
    # Minimal smoke test / usage example.
    sample_records = [
        {
            "ConfirmationNumber": "ABC244654345",
            "ContractID": "H0001",
            "PBPID": "001",
            "SegmentID": "000",
            "MemberFirstName": "John",
            "MemberLastName": "Smith",
            "MemberBirthDate": "07131936",
            "MemberGender": "M",
            "MemberMBI": "1AB2CD3FG45",
            "TransactionType": "61",
            "EnrollmentPlanYear": "2026",
        }
    ]
    out = write_eaf(sample_records, "sample_output.eaf")
    print(f"Wrote {out} with {len(HEADER_ROW)} columns.")
