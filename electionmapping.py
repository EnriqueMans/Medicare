"""
generate_election_mapping_test_cases.py

Builds a labeled set of EAF rows - some with correct Election Type <->
dependent-field mappings, some deliberately broken - so you can confirm
validate_election_dependencies.py actually catches what it's supposed to
catch (and only that).

Each case has an ExpectedLabel ('Correct' or 'Incorrect') and, for the
incorrect ones, which rule (R1-R12, from validate_election_dependencies.py)
it's designed to trip. Running this script also runs the validator against
its own output and reports whether the validator's findings matched the
expected labels - i.e. it's a test of the test.

Date convention: dates are computed relative to today's date, not hardcoded.
  - EffectiveDate (73)                 = 1st of the CURRENT month
  - SubmitDate (2) / Application Sign
    Date (75) / receipt-date inputs    = the 15th of the PRIOR month
  - Medicare Part A/B/D entitlement
    dates (28, 29, 151)                = the 15th of the PRIOR month
    (i.e. "entitlement started the same time they applied")
  This keeps the file's dates realistic and self-consistent (an app date
  in the prior month naturally produces an effective date of the 1st of
  this month under the generic "1st of month after app date" rule used
  by ICEP/IEP/IEP2/MAOEP/SEPS/SEPU/SEPV), and means the test file stays
  current every time you run it rather than aging into the past.
  AEP is the one exception left on a fixed date, since its own rule only
  fires for receipt dates between Oct 15-Dec 7 regardless of "today."

Depends on (same directory):
  - build_eaf_scenarios.py            (FIELD_NAMES, NUM_FIELDS, _row)
  - validate_election_dependencies.py (validate_dataframe)

Usage:
    python generate_election_mapping_test_cases.py
        -> writes eaf_election_mapping_cases.txt (tab-delimited EAF file)
           and eaf_election_mapping_cases_manifest.csv (ScenarioID,
           ElectionType, ExpectedLabel, RuleTested, Description), then
           runs the validator and prints a match/mismatch report.
"""

from datetime import date

import pandas as pd

from build_eaf_scenarios import FIELD_NAMES, NUM_FIELDS, _row
from validate_election_dependencies import validate_dataframe

COL = FIELD_NAMES


def _mmddyyyy(d: date) -> str:
    return f'{d.month:02d}{d.day:02d}{d.year:04d}'


def _first_of_month(d: date) -> date:
    return date(d.year, d.month, 1)


def _prior_month(d: date) -> date:
    if d.month == 1:
        return date(d.year - 1, 12, 1)
    return date(d.year, d.month - 1, 1)


_today = date.today()
EFFECTIVE_DATE = _mmddyyyy(_first_of_month(_today))          # 1st of current month
_prior = _prior_month(_today)
APP_DATE = _mmddyyyy(date(_prior.year, _prior.month, 15))    # 15th of prior month
ENTITLEMENT_DATE = APP_DATE                                   # Medicare Part A/B/D: same convention


# Each case: (id, election_type, expected_label, rule_tested, description, overrides)
CASES = [
    # ---- Correct mappings, one per election type family -----------------
    ('C01', 'AEP', 'Correct', None,
     'AEP with TC 61 and a populated Effective Date - nothing else required. '
     '(AEP keeps its own fixed Oct15-Dec7 receipt window/01-01 effective '
     'date rather than the current/prior-month convention, since that is '
     'the rule per the guide.)',
     {1: '1', 2: '11052026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000201',
      73: '01012027', 74: '61', 78: 'AEP'}),

    ('C02', 'ICEP', 'Correct', None,
     'ICEP with New to Medicare = YES and Part B entitlement date (prior '
     'month) populated; effective date is 1st of current month.',
     {1: '2', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000202',
      73: EFFECTIVE_DATE, 74: '61', 78: 'ICEP', 29: ENTITLEMENT_DATE, 125: 'YES'}),

    ('C03', 'IEP', 'Correct', None,
     'IEP with MemberBirthDate populated; app date prior month, effective '
     'date 1st of current month.',
     {1: '3', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000203',
      73: EFFECTIVE_DATE, 74: '61', 78: 'IEP', 10: '05151961'}),

    ('C04', 'IEP2', 'Correct', None,
     'IEP2 with MemberBirthDate and Part A entitlement date (prior month) '
     'populated; effective date 1st of current month.',
     {1: '4', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000204',
      73: EFFECTIVE_DATE, 74: '61', 78: 'IEP2', 10: '05011961', 28: ENTITLEMENT_DATE}),

    ('C05', 'MAOEP', 'Correct', None,
     'MAOEP with "Is MAOEP" (168) = Y; receipt prior month, effective '
     'date 1st of current month.',
     {1: '5', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000205',
      73: EFFECTIVE_DATE, 74: '61', 78: 'MAOEP', 168: 'Y'}),

    ('C06', 'SEPS', 'Correct', None,
     'SEPS with a qualifying attestation date (Lost drug coverage, 133, '
     'prior month) and a SEPS Reason code (142) populated; effective '
     'date 1st of current month.',
     {1: '6', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000206',
      73: EFFECTIVE_DATE, 74: '61', 78: 'SEPS', 133: APP_DATE, 142: '22'}),

    ('C07', 'SEPW', 'Correct', None,
     'SEPW with "Leaving employer or union" (134, prior month) populated; '
     'effective date 1st of current month.',
     {1: '7', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000207',
      73: EFFECTIVE_DATE, 74: '61', 78: 'SEPW', 134: APP_DATE}),

    ('C08', 'SEPR', 'Correct', None,
     'SEPR (no-automation type) with no attestation fields populated - '
     'exactly as the Exceptions table says it should look.',
     {1: '8', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000208',
      73: EFFECTIVE_DATE, 74: '61', 78: 'SEPR'}),

    ('C09', 'SEPU', 'Correct', None,
     'SEPU with "Extra help for premiums" (128) populated; effective '
     'date 1st of current month.',
     {1: '19', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000219',
      73: EFFECTIVE_DATE, 74: '61', 78: 'SEPU', 128: 'YES'}),

    ('C10', 'SEPV', 'Correct', None,
     'SEPV with "Recently moved" (126, prior month) populated; effective '
     'date 1st of current month.',
     {1: '20', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000220',
      73: EFFECTIVE_DATE, 74: '61', 78: 'SEPV', 126: APP_DATE}),

    # ---- Incorrect mappings, one per rule --------------------------------
    ('X01', 'AEP', 'Incorrect', 'R1',
     'AEP assigned on a disenrollment (TC 51) instead of an enrollment (TC 61).',
     {1: '9', 2: '11052026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000209',
      73: '01012027', 74: '51', 78: 'AEP'}),

    ('X02', 'ICEP', 'Incorrect', 'R2',
     'ICEP assigned with no Effective Date populated.',
     {1: '10', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000210',
      74: '61', 78: 'ICEP', 125: 'YES', 29: ENTITLEMENT_DATE}),

    ('X03', 'ICEP', 'Incorrect', 'R3',
     'ICEP assigned with "New to Medicare" left blank and no Part A/B '
     'entitlement date - neither prerequisite is met.',
     {1: '11', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000211',
      73: EFFECTIVE_DATE, 74: '61', 78: 'ICEP'}),

    ('X04', 'IEP', 'Incorrect', 'R4',
     'IEP assigned with MemberBirthDate left blank.',
     {1: '12', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000212',
      73: EFFECTIVE_DATE, 74: '61', 78: 'IEP'}),

    ('X05', 'MAOEP', 'Incorrect', 'R5',
     'MAOEP assigned but "Is MAOEP" (168) left blank instead of Y.',
     {1: '13', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000213',
      73: EFFECTIVE_DATE, 74: '61', 78: 'MAOEP'}),

    ('X06', 'AEP', 'Incorrect', 'R6',
     '"Is MAOEP" (168) = Y but Election Type is AEP, not MAOEP.',
     {1: '14', 2: '11052026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000214',
      73: '01012027', 74: '61', 78: 'AEP', 168: 'Y'}),

    ('X07', 'SEPS', 'Incorrect', 'R7',
     'SEPS assigned with no attestation field and no SEPS Reason populated.',
     {1: '15', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000215',
      73: EFFECTIVE_DATE, 74: '61', 78: 'SEPS'}),

    ('X08', 'AEP', 'Incorrect', 'R8',
     'SEPS Reason (142) populated on an AEP row (SEPS Reason should only '
     'accompany SEPS).',
     {1: '16', 2: '11052026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000216',
      73: '01012027', 74: '61', 78: 'AEP', 142: '22'}),

    ('X09', 'SEPW', 'Incorrect', 'R9',
     'SEPW assigned with "Leaving employer or union" (134) left blank.',
     {1: '17', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000217',
      73: EFFECTIVE_DATE, 74: '61', 78: 'SEPW'}),

    ('X10', 'SEPR', 'Incorrect', 'R10',
     'SEPR (no-automation type) with "New to Medicare" (125) populated, '
     'which should never be set for a type that bypasses the automation engine.',
     {1: '18', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000218',
      73: EFFECTIVE_DATE, 74: '61', 78: 'SEPR', 125: 'YES'}),

    ('X11', 'SEPU', 'Incorrect', 'R11',
     'SEPU assigned with none of the Extra Help / LIS fields (128, 129, 130) populated.',
     {1: '21', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000221',
      73: EFFECTIVE_DATE, 74: '61', 78: 'SEPU'}),

    ('X12', 'SEPV', 'Incorrect', 'R12',
     'SEPV assigned with "Recently moved" (126) left blank.',
     {1: '22', 2: APP_DATE, 3: 'H1234', 4: '001', 5: '001', 68: 'M0000222',
      73: EFFECTIVE_DATE, 74: '61', 78: 'SEPV'}),
]


def build_dataframe() -> pd.DataFrame:
    header = [COL[i] for i in range(1, NUM_FIELDS + 1)]
    rows = [_row(overrides) for _id, _et, _lbl, _rule, _desc, overrides in CASES]
    return pd.DataFrame(rows, columns=header)


def build_manifest() -> pd.DataFrame:
    return pd.DataFrame([
        dict(ScenarioID=cid, ElectionType=et, ExpectedLabel=label,
             RuleTested=rule, Description=desc)
        for cid, et, label, rule, desc, _ in CASES
    ])


def write_eaf_file(path: str = 'eaf_election_mapping_cases.txt') -> None:
    df = build_dataframe()
    df.to_csv(path, sep='\t', index=False)


if __name__ == '__main__':
    write_eaf_file('eaf_election_mapping_cases.txt')
    manifest = build_manifest()
    manifest.to_csv('eaf_election_mapping_cases_manifest.csv', index=False)

    print(f'Wrote {len(CASES)} labeled cases to eaf_election_mapping_cases.txt')
    print('Wrote eaf_election_mapping_cases_manifest.csv\n')

    # Self-check: run the validator against our own labeled cases and
    # confirm it flags exactly the rows/rules we expect it to.
    df = build_dataframe()
    df.index = [c[0] for c in CASES]  # index rows by ScenarioID for readable output
    violations = validate_dataframe(df)

    print('--- Validator self-check ---')
    mismatches = 0
    for cid, et, expected_label, rule_tested, desc, _ in CASES:
        row_violations = violations[violations['RowIndex'] == cid]
        got_flagged = len(row_violations) > 0
        should_be_flagged = expected_label == 'Incorrect'
        ok = got_flagged == should_be_flagged
        if not ok:
            mismatches += 1
        rule_hit = ', '.join(row_violations['Rule'].tolist()) if got_flagged else '-'
        status = 'OK' if ok else 'MISMATCH'
        print(f'{cid:5} {et:6} expected={expected_label:10} '
              f'rule_tested={str(rule_tested):4} validator_flagged={rule_hit:6} [{status}]')

    print(f'\n{len(CASES) - mismatches}/{len(CASES)} cases matched expectations.')
    if mismatches:
        print(f'{mismatches} mismatch(es) - review validate_election_dependencies.py rules above.')
