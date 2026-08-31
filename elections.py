"""
generate_election_mapping_test_cases.py

Builds a labeled set of EAF rows - some with correct Election Type <->
dependent-field mappings, some deliberately broken - so you can confirm
validate_election_dependencies.py actually catches what it's supposed to
catch (and only that).

Each case has an ExpectedLabel ('Correct' or 'Incorrect') and, for the
incorrect ones, which rule (R1-R10, from validate_election_dependencies.py)
it's designed to trip. Running this script also runs the validator against
its own output and reports whether the validator's findings matched the
expected labels - i.e. it's a test of the test.

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

import pandas as pd

from build_eaf_scenarios import FIELD_NAMES, NUM_FIELDS, _row
from validate_election_dependencies import validate_dataframe

COL = FIELD_NAMES

# Each case: (id, election_type, expected_label, rule_tested, description, overrides)
CASES = [
    # ---- Correct mappings, one per election type family -----------------
    ('C01', 'AEP', 'Correct', None,
     'AEP with TC 61 and a populated Effective Date - nothing else required.',
     {1: '1', 2: '11052026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000201',
      73: '01012027', 74: '61', 78: 'AEP'}),

    ('C02', 'ICEP', 'Correct', None,
     'ICEP with New to Medicare = YES and Part B entitlement date populated.',
     {1: '2', 2: '03102026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000202',
      73: '06012026', 74: '61', 78: 'ICEP', 29: '06012026', 125: 'YES'}),

    ('C03', 'IEP', 'Correct', None,
     'IEP with MemberBirthDate populated.',
     {1: '3', 2: '03012026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000203',
      73: '05012026', 74: '61', 78: 'IEP', 10: '05151961'}),

    ('C04', 'IEP2', 'Correct', None,
     'IEP2 with MemberBirthDate populated.',
     {1: '4', 2: '02012026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000204',
      73: '05012026', 74: '61', 78: 'IEP2', 10: '05011961'}),

    ('C05', 'MAOEP', 'Correct', None,
     'MAOEP with "Is MAOEP" (168) = Y.',
     {1: '5', 2: '02102026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000205',
      73: '03012026', 74: '61', 78: 'MAOEP', 168: 'Y'}),

    ('C06', 'SEPS', 'Correct', None,
     'SEPS with a qualifying attestation date (Lost drug coverage, 133) '
     'and a SEPS Reason code (142) populated.',
     {1: '6', 2: '07152026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000206',
      73: '08012026', 74: '61', 78: 'SEPS', 133: '06302026', 142: '22'}),

    ('C07', 'SEPW', 'Correct', None,
     'SEPW with "Leaving employer or union" (134) populated.',
     {1: '7', 2: '08012026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000207',
      73: '09012026', 74: '61', 78: 'SEPW', 134: '07312026'}),

    ('C08', 'SEPR', 'Correct', None,
     'SEPR (no-automation type) with no attestation fields populated - '
     'exactly as the Exceptions table says it should look.',
     {1: '8', 2: '03052026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000208',
      73: '04012026', 74: '61', 78: 'SEPR'}),

    # ---- Incorrect mappings, one per rule --------------------------------
    ('X01', 'AEP', 'Incorrect', 'R1',
     'AEP assigned on a disenrollment (TC 51) instead of an enrollment (TC 61).',
     {1: '9', 2: '11052026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000209',
      73: '01012027', 74: '51', 78: 'AEP'}),

    ('X02', 'ICEP', 'Incorrect', 'R2',
     'ICEP assigned with no Effective Date populated.',
     {1: '10', 2: '03102026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000210',
      74: '61', 78: 'ICEP', 125: 'YES', 29: '06012026'}),

    ('X03', 'ICEP', 'Incorrect', 'R3',
     'ICEP assigned with "New to Medicare" left blank and no Part A/B '
     'entitlement date - neither prerequisite is met.',
     {1: '11', 2: '03102026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000211',
      73: '06012026', 74: '61', 78: 'ICEP'}),

    ('X04', 'IEP', 'Incorrect', 'R4',
     'IEP assigned with MemberBirthDate left blank.',
     {1: '12', 2: '03012026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000212',
      73: '05012026', 74: '61', 78: 'IEP'}),

    ('X05', 'MAOEP', 'Incorrect', 'R5',
     'MAOEP assigned but "Is MAOEP" (168) left blank instead of Y.',
     {1: '13', 2: '02102026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000213',
      73: '03012026', 74: '61', 78: 'MAOEP'}),

    ('X06', 'AEP', 'Incorrect', 'R6',
     '"Is MAOEP" (168) = Y but Election Type is AEP, not MAOEP.',
     {1: '14', 2: '11052026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000214',
      73: '01012027', 74: '61', 78: 'AEP', 168: 'Y'}),

    ('X07', 'SEPS', 'Incorrect', 'R7',
     'SEPS assigned with no attestation field and no SEPS Reason populated.',
     {1: '15', 2: '07152026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000215',
      73: '08012026', 74: '61', 78: 'SEPS'}),

    ('X08', 'AEP', 'Incorrect', 'R8',
     'SEPS Reason (142) populated on an AEP row (SEPS Reason should only '
     'accompany SEPS).',
     {1: '16', 2: '11052026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000216',
      73: '01012027', 74: '61', 78: 'AEP', 142: '22'}),

    ('X09', 'SEPW', 'Incorrect', 'R9',
     'SEPW assigned with "Leaving employer or union" (134) left blank.',
     {1: '17', 2: '08012026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000217',
      73: '09012026', 74: '61', 78: 'SEPW'}),

    ('X10', 'SEPR', 'Incorrect', 'R10',
     'SEPR (no-automation type) with "New to Medicare" (125) populated, '
     'which should never be set for a type that bypasses the automation engine.',
     {1: '18', 2: '03052026', 3: 'H1234', 4: '001', 5: '001', 68: 'M0000218',
      73: '04012026', 74: '61', 78: 'SEPR', 125: 'YES'}),
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
