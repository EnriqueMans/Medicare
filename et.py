"""
assign_and_validate_election_types.py

Randomly assigns CMS Election Type values to a DataFrame, then validates
them against Application Date, Effective Date, SEPS Reason, and now
attestation fields - the beneficiary-attested answers that actually
justify a given Election Type per the EAM Appendices Guide's "Election
Period Automation Logic" section.

Attestation columns (all optional - a rule is only checked if its column
exists in your DataFrame; missing columns are silently skipped rather
than treated as failures):
  NewToMedicare        Y/N flag   - required YES for ICEP
  MemberBirthDate      date       - required for IEP / IEP2
  IsMAOEP               Y/N flag   - required Y for MAOEP
  RecentlyMoved         date       - required for SEPV
  LeavingEmployer       date       - required for SEPW
  ExtraHelp             Y/N flag   - required for SEPU
  LongTermCare          date       \\
  LeftPACE              date        \\  at least ONE of these five (or a
  LostDrugCoverage      date        /  SEPS Reason) required for SEPS
  PlanEndingContract    Y/N flag   /
  DisenrolledSNP         date      /

Rules checked here:
  V1  Election Type must be a recognized CMS code (see ELECTION_TYPES)
  V2  Election Type populated -> Effective Date must be populated
  V3  Effective Date must not be before Application Date
  V4  SEPS Reason populated -> Election Type must be SEPS
  V5  Election Type == SEPS -> SEPS Reason should be populated (warning;
      V7 below is the hard-fail version once attestation columns exist)
  V6  Election Type == AEP -> Application Date should fall within the
      Oct 15 - Dec 7 AEP receipt window
  V7  Election Type == SEPS -> at least one SEPS attestation field
      (LongTermCare/LeftPACE/LostDrugCoverage/PlanEndingContract/
      DisenrolledSNP) or SEPS Reason must be populated
  V8  Election Type == SEPW -> LeavingEmployer must be populated
  V9  Election Type == SEPV -> RecentlyMoved must be populated
  V10 Election Type == SEPU -> ExtraHelp must be populated
  V11 Election Type == ICEP -> NewToMedicare must be YES
  V12 Election Type == MAOEP -> IsMAOEP must be Y
  V13 Election Type in (IEP, IEP2) -> MemberBirthDate must be populated
  V14 Any populated attestation date must not be AFTER Application Date
      (you can't attest to a life event that hasn't happened yet as of
      the application)

Usage:
    python assign_and_validate_election_types.py
        -> runs a demo: builds a small sample DataFrame with attestation
           columns, randomly assigns Election Type, validates it, and
           prints the results.

    from assign_and_validate_election_types import (
        assign_random_election_types, validate_election_types)

    df = pd.read_csv('my_eaf_extract.csv')          # has AppDate, EffDate,
                                                       # and any attestation columns
    df = assign_random_election_types(df, seed=42)   # adds ElectionType
    violations = validate_election_types(df)         # checks it
"""

import random
from datetime import date, timedelta

import pandas as pd

# Abbreviation -> (relative weight, obsolete?), from the CMS Election
# Types table. Weights are illustrative, not CMS data - edit freely.
ELECTION_TYPES = {
    'AEP':    (30, False), 'ICEP':   (20, False), 'IEP':  (10, False),
    'IEP2':   (2,  False), 'MAOEP':  (10, False),  'SEPS': (10, False),
    'SEPW':   (4,  False), 'SEPU':   (2,  False),  'SEPV': (2,  False),
    'SEPY':   (1,  False), 'SEPR':   (1,  False),  'SEPJ': (1,  False),
    'SEPX':   (1,  False), 'SEPZ':   (2,  False),  'SEPC': (1,  False),
    'SEPL':   (1,  False), 'SEPP':   (1,  False),  'SEPQ': (1,  False),
    'OEPI':   (1,  False),
    'MADP':   (1,  True), 'OEPNEW': (1,  True), 'OEP': (1,  True),
}


def assign_random_election_types(df: pd.DataFrame, column: str = 'ElectionType',
                                  seed: int = None, uniform: bool = False,
                                  include_obsolete: bool = False) -> pd.DataFrame:
    """Return a copy of df with `column` filled with randomly-assigned
    CMS Election Type codes."""
    rng = random.Random(seed)
    choices = {k: w for k, (w, obsolete) in ELECTION_TYPES.items()
               if include_obsolete or not obsolete}
    types = list(choices.keys())
    weights = None if uniform else [choices[t] for t in types]

    out = df.copy()
    out[column] = [rng.choices(types, weights=weights, k=1)[0] for _ in range(len(out))]
    return out


def _parse_date(val):
    """Parse a date that might be MMDDYYYY, a real date/datetime, or
    blank/NaN. Returns a date object, or None if unparseable/blank."""
    if pd.isna(val) or str(val).strip() == '':
        return None
    s = str(val).strip()
    if s.isdigit() and len(s) == 8:
        try:
            return date(int(s[4:8]), int(s[0:2]), int(s[2:4]))
        except ValueError:
            return None
    parsed = pd.to_datetime(s, errors='coerce')
    return parsed.date() if not pd.isna(parsed) else None


def _truthy(val) -> bool:
    """Treat YES/Y/TRUE (case-insensitive) as an affirmative flag."""
    return str(val).strip().upper() in ('YES', 'Y', 'TRUE', '1')


def _populated(val) -> bool:
    return not (pd.isna(val) or str(val).strip() == '')


def validate_election_types(df: pd.DataFrame,
                             app_date_col: str = 'AppDate',
                             eff_date_col: str = 'EffDate',
                             election_type_col: str = 'ElectionType',
                             seps_reason_col: str = 'SEPSReason',
                             new_to_medicare_col: str = 'NewToMedicare',
                             member_birth_date_col: str = 'MemberBirthDate',
                             is_maoep_col: str = 'IsMAOEP',
                             recently_moved_col: str = 'RecentlyMoved',
                             leaving_employer_col: str = 'LeavingEmployer',
                             extra_help_col: str = 'ExtraHelp',
                             long_term_care_col: str = 'LongTermCare',
                             left_pace_col: str = 'LeftPACE',
                             lost_drug_coverage_col: str = 'LostDrugCoverage',
                             plan_ending_contract_col: str = 'PlanEndingContract',
                             disenrolled_snp_col: str = 'DisenrolledSNP') -> pd.DataFrame:
    """Check each row's Election Type against App Date / Eff Date / SEPS
    Reason plus whichever attestation columns are present in df. Any
    attestation column not present in df is simply skipped (its rule is
    not evaluated), so this works fine on your current 4-column df and
    keeps working as you add attestation columns over time.
    Returns a DataFrame of violations (empty if all rows pass)."""
    violations = []

    seps_attestation_cols = [long_term_care_col, left_pace_col,
                              lost_drug_coverage_col, plan_ending_contract_col,
                              disenrolled_snp_col]
    all_attestation_date_cols = [member_birth_date_col, recently_moved_col,
                                  leaving_employer_col, long_term_care_col,
                                  left_pace_col, lost_drug_coverage_col,
                                  disenrolled_snp_col]

    for idx, row in df.iterrows():
        et = str(row.get(election_type_col, '') or '').strip()
        seps_reason = str(row.get(seps_reason_col, '') or '').strip()
        app_raw = row.get(app_date_col, '')
        eff_raw = row.get(eff_date_col, '')
        app_date = _parse_date(app_raw)
        eff_date = _parse_date(eff_raw)

        def flag(rule, severity, message):
            violations.append(dict(RowIndex=idx, ElectionType=et, Rule=rule,
                                    Severity=severity, Message=message))

        if not et:
            continue

        # V1 - recognized code
        if et not in ELECTION_TYPES:
            flag('V1', 'Fail', f'"{et}" is not a recognized CMS Election Type code')

        # V2 - effective date required
        if not _populated(eff_raw):
            flag('V2', 'Fail', 'Election Type set but Effective Date is blank')

        # V3 - chronological sanity
        if app_date and eff_date and eff_date < app_date:
            flag('V3', 'Fail', f'Effective Date ({eff_date}) is before '
                                f'Application Date ({app_date})')

        # V4 - SEPS Reason only with SEPS
        if seps_reason and et != 'SEPS':
            flag('V4', 'Warning', f'SEPS Reason "{seps_reason}" populated but '
                                   f'Election Type is "{et}", not SEPS')

        # V5 - SEPS should have a reason (soft version; V7 is the hard version)
        if et == 'SEPS' and not seps_reason:
            flag('V5', 'Warning', 'Election Type is SEPS but SEPS Reason is blank')

        # V6 - AEP receipt window (Oct 15 - Dec 7)
        if et == 'AEP' and app_date:
            window_start = date(app_date.year, 10, 15)
            window_end = date(app_date.year, 12, 7)
            if not (window_start <= app_date <= window_end):
                flag('V6', 'Fail', f'AEP requires Application Date within '
                                    f'Oct 15-Dec 7; got {app_date}')

        # V7 - SEPS attestation
        if et == 'SEPS' and any(c in df.columns for c in seps_attestation_cols + [seps_reason_col]):
            attestation_present = any(
                c in df.columns and _populated(row.get(c, '')) for c in seps_attestation_cols
            )
            if not attestation_present and not seps_reason:
                flag('V7', 'Fail', 'SEPS requires at least one attestation field '
                                    '(LongTermCare/LeftPACE/LostDrugCoverage/'
                                    'PlanEndingContract/DisenrolledSNP) or a '
                                    'SEPS Reason to be populated')

        # V8 - SEPW
        if et == 'SEPW' and leaving_employer_col in df.columns:
            if not _populated(row.get(leaving_employer_col, '')):
                flag('V8', 'Fail', 'SEPW requires LeavingEmployer to be populated')

        # V9 - SEPV
        if et == 'SEPV' and recently_moved_col in df.columns:
            if not _populated(row.get(recently_moved_col, '')):
                flag('V9', 'Fail', 'SEPV requires RecentlyMoved to be populated')

        # V10 - SEPU
        if et == 'SEPU' and extra_help_col in df.columns:
            if not _populated(row.get(extra_help_col, '')):
                flag('V10', 'Fail', 'SEPU requires ExtraHelp to be populated')

        # V11 - ICEP
        if et == 'ICEP' and new_to_medicare_col in df.columns:
            if not _truthy(row.get(new_to_medicare_col, '')):
                flag('V11', 'Fail', f'ICEP requires NewToMedicare == YES, got '
                                     f'"{row.get(new_to_medicare_col, "")}"')

        # V12 - MAOEP
        if et == 'MAOEP' and is_maoep_col in df.columns:
            if not _truthy(row.get(is_maoep_col, '')):
                flag('V12', 'Fail', f'MAOEP requires IsMAOEP == Y, got '
                                     f'"{row.get(is_maoep_col, "")}"')

        # V13 - IEP / IEP2
        if et in ('IEP', 'IEP2') and member_birth_date_col in df.columns:
            if not _populated(row.get(member_birth_date_col, '')):
                flag('V13', 'Fail', f'{et} requires MemberBirthDate to be populated')

        # V14 - attestation date can't be after the application date
        if app_date:
            for col in all_attestation_date_cols:
                if col in df.columns and col != member_birth_date_col:
                    att_date = _parse_date(row.get(col, ''))
                    if att_date and att_date > app_date:
                        flag('V14', 'Warning', f'{col} ({att_date}) is after '
                                                f'Application Date ({app_date})')

    return pd.DataFrame(violations, columns=['RowIndex', 'ElectionType', 'Rule',
                                              'Severity', 'Message'])


if __name__ == '__main__':
    # Demo: a sample DataFrame with App/Eff/SEPSReason plus attestation columns.
    today = date.today()
    d45, d60, d10 = (today - timedelta(days=45)), (today - timedelta(days=60)), (today - timedelta(days=10))

    sample = pd.DataFrame({
        'AppDate':          [d45, '11012026', '06152026', d45, d45, d45, d45, d45],
        'EffDate':          [today, '01012027', '', d60, today, today, today, today],
        'SEPSReason':       ['', '', '', '22', '', '', '', ''],
        'NewToMedicare':    ['', '', '', '', 'YES', '', '', ''],
        'MemberBirthDate':  ['', '', '', '', '', '05151961', '', ''],
        'IsMAOEP':          ['', '', '', '', '', '', 'Y', ''],
        'RecentlyMoved':    ['', '', '', '', '', '', '', ''],
        'LeavingEmployer':  ['', '', '', '', '', '', '', ''],
        'ExtraHelp':        ['', '', '', '', '', '', '', ''],
        'LongTermCare':     ['', '', '', '', '', '', '', ''],
        'LeftPACE':         ['', '', '', '', '', '', '', ''],
        'LostDrugCoverage': ['', '', '', '', '', '', '', d10],  # will trigger V14 if AppDate < this
        'PlanEndingContract': ['', '', '', '', '', '', '', ''],
        'DisenrolledSNP':   ['', '', '', '', '', '', '', ''],
    })
    for c in ['AppDate', 'EffDate']:
        sample[c] = sample[c].apply(lambda v: v.strftime('%m%d%Y') if hasattr(v, 'strftime') else v)
    sample['LostDrugCoverage'] = sample['LostDrugCoverage'].apply(
        lambda v: v.strftime('%m%d%Y') if hasattr(v, 'strftime') else v)

    df = assign_random_election_types(sample, seed=1)
    # Force specific types so the demo output is illustrative of each rule
    df.loc[1, 'ElectionType'] = 'AEP'      # inside window -> clean
    df.loc[2, 'ElectionType'] = 'AEP'      # outside window -> V6
    df.loc[3, 'ElectionType'] = 'SEPS'     # has reason, no attestation -> clean (V5/V7 satisfied)
    df.loc[4, 'ElectionType'] = 'ICEP'     # NewToMedicare = YES -> clean
    df.loc[5, 'ElectionType'] = 'IEP'      # MemberBirthDate populated -> clean
    df.loc[6, 'ElectionType'] = 'MAOEP'    # IsMAOEP = Y -> clean
    df.loc[7, 'ElectionType'] = 'SEPS'     # LostDrugCoverage populated but AFTER AppDate -> V14

    print('Sample DataFrame with randomly-assigned Election Types:')
    print(df.to_string(index=False))

    violations = validate_election_types(df)
    print(f'\n{len(violations)} violation(s) found:\n')
    if len(violations):
        print(violations.to_string(index=False))
    else:
        print('None.')
