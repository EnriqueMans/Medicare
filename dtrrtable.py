DTRR_FIELDS = [
    {"item": "1", "field": "Beneficiary ID (HICN/MBI)", "size": 12, "position": "1-12"},
    {"item": "2", "field": "Surname", "size": 12, "position": "13-24"},
    {"item": "3", "field": "First Name", "size": 7, "position": "25-31"},
    {"item": "4", "field": "Middle Initial", "size": 1, "position": "32"},
    {"item": "5", "field": "Sex Code", "size": 1, "position": "33"},
    {"item": "6", "field": "Date of Birth", "size": 8, "position": "34-41"},
    {"item": "7", "field": "Record Type", "size": 1, "position": "42"},
    {"item": "8", "field": "Contract Number", "size": 5, "position": "43-47"},
    {"item": "9", "field": "State Code", "size": 2, "position": "48-49"},
    {"item": "10", "field": "County Code", "size": 3, "position": "50-52"},
    {"item": "11", "field": "Disability Indicator", "size": 1, "position": "53"},
    {"item": "12", "field": "Hospice Indicator", "size": 1, "position": "54"},
    {"item": "13", "field": "Institutional/NHC/HCBS Indicator", "size": 1, "position": "55"},
    {"item": "14", "field": "ESRD Indicator", "size": 1, "position": "56"},
    {"item": "15", "field": "Transaction Reply Code (TRC)", "size": 3, "position": "57-59"},
    {"item": "16", "field": "Transaction Code (TC)", "size": 2, "position": "60-61"},
    {"item": "17", "field": "Entitlement Type Code", "size": 1, "position": "62"},
    {"item": "18", "field": "Effective Date", "size": 8, "position": "63-70"},
    {"item": "19", "field": "WA Indicator", "size": 1, "position": "71"},
    {"item": "20", "field": "Plan Benefit Package ID", "size": 3, "position": "72-74"},
    {"item": "21", "field": "Filler", "size": 1, "position": "75"},
    {"item": "22", "field": "Transaction Date", "size": 8, "position": "76-83"},
    {"item": "23", "field": "UI Initiated Change Flag", "size": 1, "position": "84"},
    {"item": "24", "field": "TRC-dependent field (see sub-items a-gg)", "size": 12, "position": "85-96"},
    {"item": "24a", "field": "Effective Date of the Disenrollment", "size": 8, "position": "85-92"},
    {"item": "24b", "field": "New Enrollment Effective Date", "size": 8, "position": "85-92"},
    {"item": "24c", "field": "Claim Number (old)", "size": 12, "position": "85-96"},
    {"item": "24d", "field": "Date of Death", "size": 8, "position": "85-92"},
    {"item": "24e", "field": "Hospice End Date", "size": 8, "position": "85-92"},
    {"item": "24f", "field": "ESRD Start Date", "size": 8, "position": "85-92"},
    {"item": "24g", "field": "ESRD End Date", "size": 8, "position": "85-92"},
    {"item": "24h", "field": "Institutional/NHC Start Date", "size": 8, "position": "85-92"},
    {"item": "24i", "field": "Medicaid Start Date", "size": 8, "position": "85-92"},
    {"item": "24j", "field": "Medicaid End Date", "size": 8, "position": "85-92"},
    {"item": "24k", "field": "Part A End Date", "size": 8, "position": "85-92"},
    {"item": "24l", "field": "WA Start Date", "size": 8, "position": "85-92"},
    {"item": "24m", "field": "WA End Date", "size": 8, "position": "85-92"},
    {"item": "24n", "field": "Part A Reinstate Date", "size": 8, "position": "85-92"},
    {"item": "24o", "field": "Part B End Date", "size": 8, "position": "85-92"},
    {"item": "24p", "field": "Part B Reinstate Date", "size": 8, "position": "85-92"},
    {"item": "24q", "field": "Old State and County Codes", "size": 5, "position": "85-89"},
    {"item": "24r", "field": "Attempted Enroll Effective Date", "size": 8, "position": "85-92"},
    {"item": "24s", "field": "PBP Effective Date", "size": 8, "position": "85-92"},
    {"item": "24t", "field": "Correct Part D Premium Rate", "size": 12, "position": "85-96"},
    {"item": "24u", "field": "Date Identifying Information Changed by UI User", "size": 8, "position": "85-92"},
    {"item": "24v", "field": "Modified Part C Premium Amount", "size": 12, "position": "85-96"},
    {"item": "24w", "field": "Date of Death Removed", "size": 8, "position": "85-92"},
    {"item": "24x", "field": "Dialysis End Date", "size": 8, "position": "85-92"},
    {"item": "24y", "field": "Transplant Failure Date", "size": 8, "position": "85-92"},
    {"item": "24z", "field": "New ZIP Code", "size": 10, "position": "85-94"},
    {"item": "24aa", "field": "Previous Contract for POS Drug Edit or CARA Status Active Indicator", "size": 5, "position": "85-89"},
    {"item": "24bb", "field": "MSP Period Start Date", "size": 8, "position": "85-92"},
    {"item": "24cc", "field": "Maximum NUNCMO Calculated", "size": 3, "position": "85-87"},
    {"item": "24dd", "field": "IC Model End Date", "size": 8, "position": "85-92"},
    {"item": "24ee", "field": "Residence Address End Date", "size": 8, "position": "85-92"},
    {"item": "24ff", "field": "Withholding Agency Rejection Code", "size": 5, "position": "85-89"},
    {"item": "24gg", "field": "MPPP Termination Reason Code", "size": 2, "position": "85-86"},
    {"item": "25", "field": "District Office Code", "size": 3, "position": "97-99"},
    {"item": "26", "field": "Previous Part D Contract/PBP for TrOOP Transfer", "size": 8, "position": "100-107"},
    {"item": "27", "field": "SEP Reason Code", "size": 2, "position": "108-109"},
    {"item": "28", "field": "Filler", "size": 6, "position": "110-115"},
    {"item": "29", "field": "Source ID", "size": 5, "position": "116-120"},
    {"item": "30", "field": "Prior Plan Benefit Package ID", "size": 3, "position": "121-123"},
    {"item": "31", "field": "Application Date", "size": 8, "position": "124-131"},
    {"item": "32", "field": "UI User Organization Designation", "size": 2, "position": "132-133"},
    {"item": "33", "field": "Out of Area Flag", "size": 1, "position": "134"},
    {"item": "34", "field": "Segment Number", "size": 3, "position": "135-137"},
    {"item": "35", "field": "Part C Beneficiary Premium", "size": 8, "position": "138-145"},
    {"item": "36", "field": "Part D Beneficiary Premium", "size": 8, "position": "146-153"},
    {"item": "37", "field": "Election Type Code", "size": 1, "position": "154"},
    {"item": "38", "field": "Enrollment Source Code", "size": 1, "position": "155"},
    {"item": "39", "field": "Part D Opt-Out Flag", "size": 1, "position": "156"},
    {"item": "40", "field": "Premium Withhold Option/Parts C-D", "size": 1, "position": "157"},
    {"item": "41", "field": "Cumulative Number of Uncovered Months", "size": 3, "position": "158-160"},
    {"item": "42", "field": "Creditable Coverage Flag", "size": 1, "position": "161"},
    {"item": "43", "field": "Employer Subsidy Override Flag", "size": 1, "position": "162"},
    {"item": "44", "field": "Processing Timestamp", "size": 15, "position": "163-177"},
    {"item": "45", "field": "End Date", "size": 8, "position": "178-185"},
    {"item": "46", "field": "Submitted Number of Uncovered Months", "size": 3, "position": "186-188"},
    {"item": "47", "field": "Filler", "size": 7, "position": "189-195"},
    {"item": "48", "field": "Preferred Language Other Than English", "size": 1, "position": "196"},
    {"item": "49", "field": "Accessible Format", "size": 1, "position": "197"},
    {"item": "50", "field": "Secondary Drug Insurance Flag", "size": 1, "position": "198"},
    {"item": "51", "field": "Secondary Rx ID", "size": 20, "position": "199-218"},
    {"item": "52", "field": "Secondary Rx Group", "size": 15, "position": "219-233"},
    {"item": "53", "field": "EGHP", "size": 1, "position": "234"},
    {"item": "54", "field": "Part D Low-Income Premium Subsidy Level", "size": 3, "position": "235-237"},
    {"item": "55", "field": "Low-Income Co-Pay Category", "size": 1, "position": "238"},
    {"item": "56", "field": "Low-Income Period Effective Date", "size": 8, "position": "239-246"},
    {"item": "57", "field": "Part D Late Enrollment Penalty Amount", "size": 8, "position": "247-254"},
    {"item": "58", "field": "Part D Late Enrollment Penalty Waived Amount", "size": 8, "position": "255-262"},
    {"item": "59", "field": "Part D Late Enrollment Penalty Subsidy Amount", "size": 8, "position": "263-270"},
    {"item": "60", "field": "Low-Income Part D Premium Subsidy Amount", "size": 8, "position": "271-278"},
    {"item": "61", "field": "Part D Rx BIN", "size": 6, "position": "279-284"},
    {"item": "62", "field": "Part D Rx PCN", "size": 10, "position": "285-294"},
    {"item": "63", "field": "Part D Rx Group", "size": 15, "position": "295-309"},
    {"item": "64", "field": "Part D Rx ID", "size": 20, "position": "310-329"},
    {"item": "65", "field": "Secondary Rx BIN", "size": 6, "position": "330-335"},
    {"item": "66", "field": "Secondary Rx PCN", "size": 10, "position": "336-345"},
    {"item": "67", "field": "De Minimis Differential Amount", "size": 8, "position": "346-353"},
    {"item": "68", "field": "MSP Status Flag", "size": 1, "position": "354"},
    {"item": "69", "field": "Low Income Period End Date", "size": 8, "position": "355-362"},
    {"item": "70", "field": "Low Income Subsidy Source Code", "size": 1, "position": "363"},
    {"item": "71", "field": "Enrollee Type Flag, PBP Level", "size": 1, "position": "364"},
    {"item": "72", "field": "Application Date Indicator", "size": 1, "position": "365"},
    {"item": "73", "field": "TRC Short Name", "size": 15, "position": "366-380"},
    {"item": "74", "field": "Disenrollment Reason Code (DRC)", "size": 2, "position": "381-382"},
    {"item": "75", "field": "MMP Opt Out Flag", "size": 1, "position": "383"},
    {"item": "76", "field": "Cleanup ID", "size": 10, "position": "384-393"},
    {"item": "77", "field": "CARA Status Add/Update/Delete Flag", "size": 1, "position": "394"},
    {"item": "78", "field": "POS Drug Edit Status", "size": 1, "position": "395"},
    {"item": "79", "field": "Drug Class", "size": 3, "position": "396-398"},
    {"item": "80", "field": "POS Drug Edit Code", "size": 3, "position": "399-401"},
    {"item": "81", "field": "CARA Status Notification Start Date", "size": 8, "position": "402-409"},
    {"item": "82", "field": "CARA Status Implementation Start Date", "size": 8, "position": "410-417"},
    {"item": "83", "field": "CARA Status Notification End Date", "size": 8, "position": "418-425"},
    {"item": "84", "field": "Hospice Provider Number", "size": 13, "position": "426-438"},
    {"item": "85", "field": "IC Model Type Indicator", "size": 2, "position": "439-440"},
    {"item": "86", "field": "IC Model End Date Reason Code", "size": 2, "position": "441-442"},
    {"item": "87", "field": "IC Model Benefit Status", "size": 2, "position": "443-444"},
    {"item": "88", "field": "Updated Medicaid Status for Community RAF beneficiary", "size": 1, "position": "445"},
    {"item": "89", "field": "CARA Status Implementation End Date", "size": 8, "position": "446-453"},
    {"item": "90", "field": "Prescriber Limitation", "size": 1, "position": "454"},
    {"item": "91", "field": "Pharmacy Limitation", "size": 1, "position": "455"},
    {"item": "92", "field": "Filler", "size": 19, "position": "456-474"},
    {"item": "93", "field": "System Assigned Transaction Tracking ID", "size": 20, "position": "475-494"},
    {"item": "94", "field": "Plan Assigned Transaction Tracking ID", "size": 15, "position": "495-509"},
    {"item": "95", "field": "Relationship to Enrollee (see sub-items a-g)", "size": 7, "position": "510-516"},
    {"item": "95a", "field": "Agent", "size": 1, "position": "510"},
    {"item": "95b", "field": "Broker", "size": 1, "position": "511"},
    {"item": "95c", "field": "SHIP counselors", "size": 1, "position": "512"},
    {"item": "95d", "field": "Authorized representatives", "size": 1, "position": "513"},
    {"item": "95e", "field": "Other (third parties)", "size": 1, "position": "514"},
    {"item": "95f", "field": "Self", "size": 1, "position": "515"},
    {"item": "95g", "field": "Form left blank", "size": 1, "position": "516"},
    {"item": "96", "field": "National Producer Number (NPN)", "size": 10, "position": "517-526"},
    {"item": "97", "field": "OEC Indicator", "size": 1, "position": "527"},
    {"item": "98", "field": "OEC Application Date", "size": 8, "position": "528-535"},
    {"item": "99", "field": "OEC Application Number", "size": 12, "position": "536-547"},
    {"item": "100", "field": "Beneficiary Phone Number", "size": 10, "position": "548-557"},
    {"item": "101", "field": "Beneficiary Email Address", "size": 74, "position": "558-631"},
    {"item": "102", "field": "Filler", "size": 169, "position": "632-800"},
]

# ---------------------------------------------------------------------------
# Build a pandas DataFrame representation
# ---------------------------------------------------------------------------
import pandas as pd

def _parse_position(pos: str):
    """Convert a '85-92' or '33' position string to 0-indexed (start, end)
    suitable for pandas.read_fwf colspecs (end is exclusive)."""
    if "-" in pos:
        start, end = pos.split("-")
        return int(start) - 1, int(end)
    else:
        start = int(pos)
        return start - 1, start

# Only use top-level items for widths/colspecs (skip the 24x/95x sub-fields,
# since they overlap byte ranges already covered by items 24 and 95).
top_level = [f for f in DTRR_FIELDS if "." not in f["item"] and not f["item"][-1].isalpha()]

widths = [f["size"] for f in top_level]
colspecs = [_parse_position(f["position"]) for f in top_level]
columns = [f["field"] for f in top_level]

# Empty DataFrame with the correct columns (no rows yet)
dtrr_df = pd.DataFrame(columns=columns)

# Reference DataFrame of the spec itself (item / field / size / position)
dtrr_spec_df = pd.DataFrame(DTRR_FIELDS)

if __name__ == "__main__":
    print("widths:", widths)
    print("colspecs:", colspecs)
    print(dtrr_df)
    print(dtrr_spec_df.head())
