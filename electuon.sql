/* =============================================================================
   EAM Election Period Automation Logic - T-SQL Port + Self-Tests + Validation
   Source: TriZetto EAM Appendices Guide 6.10, "Election Period Automation
           Logic" (p.26-45) and "CMS Transfer File / EAF Layout" (p.89-101)

   ---------------------------------------------------------------------------
   IMPORTANT - WHAT THIS SCRIPT DOES AND DOES NOT DO
   ---------------------------------------------------------------------------
   - I do NOT have a live connection to your SQL Server instance, and this
     environment has no network access, so none of this has been executed
     against real EAM data. Run it yourself in SSMS / sqlcmd / Azure Data
     Studio against a TEST/UAT environment first.
   - CONFIRMED from the docs: table names tbtransactions and tbmemberinfo
     (from the Audit Configuration table, EAM Admin Guide p.111), and a
     field named "ElectionType" (from the CMS Transfer/Member Extract file
     layout, EAM Appendices Guide p.101 - values: AEP, IEP, ICEP, SEP, OEP,
     OEPNEW, OEPI).
   - NOT CONFIRMED: exact column names/types in tbtransactions/tbmemberinfo
     as they exist in YOUR database (e.g. whether the live column is
     ElectionType, Election_Type, ELECT_TYPE, etc.), DOB/Part A/B/D
     entitlement date column names, or whether SEP sub-type (SEPU, SEPV...)
     is stored as a separate column vs. derived from ElectionType + a reason
     code column. Section 1 (functions) is schema-independent and safe to
     deploy as-is. Section 3 (validation query) has placeholder column names
     marked with --CONFIRM-- that you must adjust to your actual schema
     before running - query the columns first (see Section 2).
   ============================================================================ */


/* =============================================================================
   SECTION 1: Scalar functions implementing the date-driven calculation rules
   ============================================================================= */

-- ---------------------------------------------------------------------------
-- AEP - Annual Election Period (doc p.27)
-- Window: receipt date between Oct 15 and Dec 7 (inclusive) of any year.
-- Effective date = Jan 1 of next year.
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_IsAepWindow (@ReceiptDate DATE)
RETURNS BIT
AS
BEGIN
    DECLARE @Yr INT = YEAR(@ReceiptDate);
    DECLARE @Start DATE = DATEFROMPARTS(@Yr, 10, 15);
    DECLARE @End   DATE = DATEFROMPARTS(@Yr, 12, 7);
    RETURN CASE WHEN @ReceiptDate BETWEEN @Start AND @End THEN 1 ELSE 0 END;
END;
GO

CREATE OR ALTER FUNCTION dbo.fn_AepEffectiveDate (@ReceiptDate DATE)
RETURNS DATE
AS
BEGIN
    RETURN CASE
        WHEN dbo.fn_IsAepWindow(@ReceiptDate) = 1
        THEN DATEFROMPARTS(YEAR(@ReceiptDate) + 1, 1, 1)
        ELSE NULL  -- not applicable outside the AEP window
    END;
END;
GO

-- ---------------------------------------------------------------------------
-- ICEP - Initial Coverage Election Period (doc p.27-29)
-- Effective date = 1st of month after app date, but not before eligibility date.
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_IcepEffectiveDate
(
    @AppDate DATE,
    @EligibilityStartDate DATE
)
RETURNS DATE
AS
BEGIN
    DECLARE @FirstOfMonthAfterApp DATE =
        DATEFROMPARTS(YEAR(DATEADD(MONTH, 1, @AppDate)), MONTH(DATEADD(MONTH, 1, @AppDate)), 1);
    DECLARE @EligibilityFirstOfMonth DATE =
        DATEFROMPARTS(YEAR(@EligibilityStartDate), MONTH(@EligibilityStartDate), 1);
    RETURN CASE
        WHEN @FirstOfMonthAfterApp > @EligibilityFirstOfMonth THEN @FirstOfMonthAfterApp
        ELSE @EligibilityFirstOfMonth
    END;
END;
GO

-- ---------------------------------------------------------------------------
-- IEP - Initial Enrollment Period for Part D (doc p.29-30)
-- If AppDate < 1st-of-month(DOB + 65yrs): effective = that 1st-of-month.
-- Else: effective = 1st of month after AppDate.
-- Same formula reused for IEP2 per doc (p.31).
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_IepEffectiveDate
(
    @AppDate DATE,
    @DOB DATE
)
RETURNS DATE
AS
BEGIN
    DECLARE @Turning65 DATE =
        DATEFROMPARTS(YEAR(@DOB) + 65, MONTH(@DOB), 1);
    DECLARE @FirstOfMonthAfterApp DATE =
        DATEFROMPARTS(YEAR(DATEADD(MONTH, 1, @AppDate)), MONTH(DATEADD(MONTH, 1, @AppDate)), 1);
    RETURN CASE
        WHEN @AppDate < @Turning65 THEN @Turning65
        ELSE @FirstOfMonthAfterApp
    END;
END;
GO

-- ---------------------------------------------------------------------------
-- IEP2 window (doc p.30-31)
-- DOB on 1st of month:      window = (Turning65 -4mo) .. EOMONTH(Turning65 +2mo)
-- DOB NOT on 1st of month:  window = (Turning65 -3mo) .. EOMONTH(Turning65 +3mo)
-- Returns 1 if @AppDate falls in the applicable window, else 0.
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_Iep2InWindow
(
    @AppDate DATE,
    @DOB DATE
)
RETURNS BIT
AS
BEGIN
    DECLARE @Turning65 DATE = DATEFROMPARTS(YEAR(@DOB) + 65, MONTH(@DOB), 1);
    DECLARE @WindowStart DATE;
    DECLARE @WindowEnd DATE;

    IF (DAY(@DOB) = 1)
    BEGIN
        SET @WindowStart = DATEADD(MONTH, -4, @Turning65);
        SET @WindowEnd   = EOMONTH(DATEADD(MONTH, 2, @Turning65));
    END
    ELSE
    BEGIN
        SET @WindowStart = DATEADD(MONTH, -3, @Turning65);
        SET @WindowEnd   = EOMONTH(DATEADD(MONTH, 3, @Turning65));
    END

    RETURN CASE WHEN @AppDate BETWEEN @WindowStart AND @WindowEnd THEN 1 ELSE 0 END;
END;
GO

-- ---------------------------------------------------------------------------
-- MAOEP basic case (doc p.31): effective = 1st of month after receipt date.
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_MaoepEffectiveDateBasic (@ReceiptDate DATE)
RETURNS DATE
AS
BEGIN
    RETURN DATEFROMPARTS(YEAR(DATEADD(MONTH, 1, @ReceiptDate)), MONTH(DATEADD(MONTH, 1, @ReceiptDate)), 1);
END;
GO

-- MAOEP Scenario B eligibility flag (doc p.31-32) - PARTIAL implementation.
-- Only checks the Jan1-Mar31 window + BEQR field 96/99 value; does NOT check
-- accepted enrollment/disenrollment counts or field 89/92 duplicate-use
-- checks (those need live TC61/TRC data - see doc for full rule).
CREATE OR ALTER FUNCTION dbo.fn_MaoepScenarioBPartialEligible
(
    @AppDate DATE,
    @BeqrField96Or99 VARCHAR(10)
)
RETURNS BIT
AS
BEGIN
    DECLARE @InWindow BIT = CASE
        WHEN @AppDate BETWEEN DATEFROMPARTS(YEAR(@AppDate), 1, 1)
                           AND DATEFROMPARTS(YEAR(@AppDate), 3, 31)
        THEN 1 ELSE 0 END;
    DECLARE @ValidCode BIT = CASE
        WHEN @BeqrField96Or99 IN ('01','02','04','05','08','09','40',
                                   '28','29','30','31','42','43','44',
                                   '46','47','48','49','50')
        THEN 1 ELSE 0 END;
    RETURN CASE WHEN @InWindow = 1 AND @ValidCode = 1 THEN 1 ELSE 0 END;
END;
GO

-- ---------------------------------------------------------------------------
-- SEPU (doc p.37): effective = 1st of month after receipt date.
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_SepuEffectiveDate (@ReceiptDate DATE)
RETURNS DATE
AS
BEGIN
    RETURN DATEFROMPARTS(YEAR(DATEADD(MONTH, 1, @ReceiptDate)), MONTH(DATEADD(MONTH, 1, @ReceiptDate)), 1);
END;
GO

-- ---------------------------------------------------------------------------
-- SEPV (doc p.38): EffectiveDate > AppDate AND EffectiveDate >= MoveDate
-- AND EffectiveDate <= 1st-of-(AppDate month + 3 months).
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_SepvIsEligible
(
    @AppDate DATE,
    @EffectiveDate DATE,
    @MoveOrReleaseDate DATE
)
RETURNS BIT
AS
BEGIN
    DECLARE @UpperBound DATE =
        DATEFROMPARTS(YEAR(DATEADD(MONTH, 3, @AppDate)), MONTH(DATEADD(MONTH, 3, @AppDate)), 1);
    RETURN CASE
        WHEN @EffectiveDate > @AppDate
         AND @EffectiveDate >= @MoveOrReleaseDate
         AND @EffectiveDate <= @UpperBound
        THEN 1 ELSE 0 END;
END;
GO

-- ---------------------------------------------------------------------------
-- SEPW (doc p.39): EffectiveDate > AppDate AND EffectiveDate <= 1st-of-
-- (AppDate month + 3 months).
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_SepwIsEligible
(
    @AppDate DATE,
    @EffectiveDate DATE
)
RETURNS BIT
AS
BEGIN
    DECLARE @UpperBound DATE =
        DATEFROMPARTS(YEAR(DATEADD(MONTH, 3, @AppDate)), MONTH(DATEADD(MONTH, 3, @AppDate)), 1);
    RETURN CASE
        WHEN @EffectiveDate > @AppDate AND @EffectiveDate <= @UpperBound
        THEN 1 ELSE 0 END;
END;
GO

-- ---------------------------------------------------------------------------
-- SEPL (doc p.39-41, worked example only): effective = 1st of month after
-- receipt date. Full Scenario A gating (field 175, CARA status, Q4
-- exclusion) is NOT implemented - needs live EAM data, see doc p.40-41.
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_SeplEffectiveDate (@ReceiptDate DATE)
RETURNS DATE
AS
BEGIN
    RETURN DATEFROMPARTS(YEAR(DATEADD(MONTH, 1, @ReceiptDate)), MONTH(DATEADD(MONTH, 1, @ReceiptDate)), 1);
END;
GO

-- ---------------------------------------------------------------------------
-- SEPQ (doc p.41, effective 2025+): effective = 1st of month after app date.
-- Gating (attestation Q9 + CARA) NOT implemented - needs live EAM data.
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_SepqEffectiveDate (@AppDate DATE)
RETURNS DATE
AS
BEGIN
    RETURN DATEFROMPARTS(YEAR(DATEADD(MONTH, 1, @AppDate)), MONTH(DATEADD(MONTH, 1, @AppDate)), 1);
END;
GO

-- ---------------------------------------------------------------------------
-- Fixed-rule election types (doc p.43)
-- ---------------------------------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_SeprEffectiveDate (@ReceiptDate DATE)
RETURNS DATE
AS
BEGIN
    RETURN DATEFROMPARTS(YEAR(DATEADD(MONTH, 1, @ReceiptDate)), MONTH(DATEADD(MONTH, 1, @ReceiptDate)), 1);
END;
GO

CREATE OR ALTER FUNCTION dbo.fn_SeppEffectiveDate (@AppDate DATE)
RETURNS DATE
AS
BEGIN
    RETURN DATEFROMPARTS(YEAR(DATEADD(MONTH, 1, @AppDate)), MONTH(DATEADD(MONTH, 1, @AppDate)), 1);
END;
GO
-- SEPJ / SEPX / SEPZ / SEPC / OEPI effective dates are simple passthroughs
-- of a beneficiary/admin/transaction-provided date - no function needed.


/* =============================================================================
   SECTION 1b: SEP Reason Code hierarchy + non-automated codes (doc p.44-45)
   ============================================================================= */

IF OBJECT_ID('tempdb..#SepReasonHierarchy') IS NOT NULL DROP TABLE #SepReasonHierarchy;
CREATE TABLE #SepReasonHierarchy
(
    ReasonCode VARCHAR(5) NOT NULL PRIMARY KEY,
    HierarchyRank INT NOT NULL,
    HasInsertDate BIT NOT NULL,
    AttestationQuestion INT NULL
);

INSERT INTO #SepReasonHierarchy (ReasonCode, HierarchyRank, HasInsertDate, AttestationQuestion) VALUES
('NEW', 1,  0, 1), ('MRD', 2,  0, NULL), ('ICE', 3,  0, NULL), ('MDE', 4,  0, 9),
('DEP', 5,  0, 9), ('OEP', 6,  0, 2),    ('LT2', 7,  0, NULL), ('LTC', 8,  1, 10),
('MCD', 9,  1, 7), ('NLS', 10, 1, 8),    ('DIF', 11, 1, 16),   ('RUS', 12, 1, 5),
('MOV', 13, 1, 3), ('INC', 14, 1, 4),    ('LEC', 15, 1, 13),   ('5ST', 16, 0, NULL),
('VIO', 17, 0, NULL), ('MYT', 18, 0, 15),('EOC', 19, 0, 15),   ('LCC', 20, 1, 12),
('CRE', 21, 0, NULL), ('SAN', 23, 0, NULL), ('PAC', 24, 1, 11),('12G', 25, 0, NULL),
('RET', 26, 0, NULL), ('SNP', 27, 1, 17), ('PAP', 28, 0, 14),  ('CSN', 30, 0, NULL),
('LAW', 31, 1, 6),  ('ACC', 32, 0, NULL), ('REC', 33, 0, NULL),('LPI', 34, 0, NULL),
('EXC', 35, 0, NULL),('12J', 36, 0, NULL),('DST', 37, 0, 18),  ('PRO', 38, 0, NULL),
('IND', 40, 0, NULL),('IIP', 41, 0, NULL),('INV', 42, 0, NULL),('OSD', 43, 0, NULL),
('OTH', 44, 0, NULL);
-- NOTE: hierarchy ranks 22 and 29 are absent in the source document itself
-- (gap in original table) - preserved as-is, not renumbered.

IF OBJECT_ID('tempdb..#SepReasonCodesNotAutomated') IS NOT NULL DROP TABLE #SepReasonCodesNotAutomated;
CREATE TABLE #SepReasonCodesNotAutomated (ReasonCode VARCHAR(5) NOT NULL PRIMARY KEY);
INSERT INTO #SepReasonCodesNotAutomated (ReasonCode) VALUES
('CSN'),('CPN'),('LPI'),('CDC'),('REC'),('ACC'),('RET'),('EXC'),('ICE'),('PRO'),
('VIO'),('IND'),('CRE'),('GEP'),('SAN'),('IIP'),('OSD'),('INV'),('INT');


/* =============================================================================
   SECTION 2: SELF-TESTS - verifying the T-SQL functions against the doc's
   own worked examples (mirrors the Python module's run_tests()).
   Run this block; every row should show Result = 'PASS'.
   ============================================================================= */

;WITH Tests AS
(
    SELECT 'AEP - receipt Oct 15 -> eff Jan 1 next yr' AS TestName,
           dbo.fn_AepEffectiveDate('2026-10-15') AS Actual,
           CAST('2027-01-01' AS DATE) AS Expected
    UNION ALL
    SELECT 'AEP - receipt Dec 7 -> eff Jan 1 next yr',
           dbo.fn_AepEffectiveDate('2026-12-07'),
           '2027-01-01'
    UNION ALL
    SELECT 'ICEP - app Mar, eligibility Jun1 -> eff Jun1 (DOB Jun16 example)',
           dbo.fn_IcepEffectiveDate('2026-03-15', '2026-06-01'),
           '2026-06-01'
    UNION ALL
    SELECT 'ICEP - app Jul -> eff = 1st of month after app',
           dbo.fn_IcepEffectiveDate('2026-07-10', '2026-06-01'),
           '2026-08-01'
    UNION ALL
    SELECT 'IEP - app before turning-65 month -> eff = 1st of turning-65 month',
           dbo.fn_IepEffectiveDate('2026-03-01', '1961-05-20'),
           '2026-05-01'
    UNION ALL
    SELECT 'IEP - app after turning-65 month -> eff = 1st of month after app',
           dbo.fn_IepEffectiveDate('2026-06-15', '1961-05-20'),
           '2026-07-01'
    UNION ALL
    SELECT 'MAOEP basic - eff = 1st of month after receipt',
           dbo.fn_MaoepEffectiveDateBasic('2026-02-10'),
           '2026-03-01'
    UNION ALL
    SELECT 'SEPU - eff = 1st of month after receipt',
           dbo.fn_SepuEffectiveDate('2026-04-05'),
           '2026-05-01'
    UNION ALL
    SELECT 'SEPL - doc worked example: Receipt Oct1 -> eff Nov1',
           dbo.fn_SeplEffectiveDate('2026-10-01'),
           '2026-11-01'
    UNION ALL
    SELECT 'SEPQ - eff = 1st of month after app date',
           dbo.fn_SepqEffectiveDate('2026-03-05'),
           '2026-04-01'
    UNION ALL
    SELECT 'SEPR - eff = 1st of month after receipt',
           dbo.fn_SeprEffectiveDate('2026-06-20'),
           '2026-07-01'
    UNION ALL
    SELECT 'SEPP - eff = 1st of following month',
           dbo.fn_SeppEffectiveDate('2026-09-10'),
           '2026-10-01'
)
SELECT
    TestName,
    Expected,
    Actual,
    CASE WHEN Expected = Actual THEN 'PASS' ELSE 'FAIL' END AS Result
FROM Tests
ORDER BY TestName;

-- Boolean-returning function tests
;WITH BoolTests AS
(
    SELECT 'AEP window - Dec8 is OUTSIDE window' AS TestName,
           dbo.fn_IsAepWindow('2026-12-08') AS Actual, 0 AS Expected
    UNION ALL
    SELECT 'IEP2 window - DOB on 1st, app in-window',
           dbo.fn_Iep2InWindow('2026-02-01', '1961-05-01'), 1
    UNION ALL
    SELECT 'IEP2 window - DOB not on 1st, app in-window',
           dbo.fn_Iep2InWindow('2026-03-01', '1961-05-20'), 1
    UNION ALL
    SELECT 'MAOEP Scenario B (partial) - in-window + valid code',
           dbo.fn_MaoepScenarioBPartialEligible('2026-02-15', '01'), 1
    UNION ALL
    SELECT 'MAOEP Scenario B (partial) - outside Jan-Mar window',
           dbo.fn_MaoepScenarioBPartialEligible('2026-05-01', '01'), 0
    UNION ALL
    SELECT 'SEPV - eligible case',
           dbo.fn_SepvIsEligible('2026-04-01', '2026-05-01', '2026-03-20'), 1
    UNION ALL
    SELECT 'SEPV - exceeds 3-month cap',
           dbo.fn_SepvIsEligible('2026-04-01', '2026-09-01', '2026-03-20'), 0
    UNION ALL
    SELECT 'SEPW - eligible case (app Apr10, eff Jul1)',
           dbo.fn_SepwIsEligible('2026-04-10', '2026-07-01'), 1
    UNION ALL
    SELECT 'SEPW - exceeds 3-month cap (app Apr10, eff Aug1)',
           dbo.fn_SepwIsEligible('2026-04-10', '2026-08-01'), 0
)
SELECT
    TestName,
    Expected,
    Actual,
    CASE WHEN Expected = Actual THEN 'PASS' ELSE 'FAIL' END AS Result
FROM BoolTests
ORDER BY TestName;

-- Hierarchy / manual-review lookup tests
SELECT
    'Hierarchy - NEW is rank 1' AS TestName,
    1 AS Expected,
    HierarchyRank AS Actual,
    CASE WHEN HierarchyRank = 1 THEN 'PASS' ELSE 'FAIL' END AS Result
FROM #SepReasonHierarchy WHERE ReasonCode = 'NEW'
UNION ALL
SELECT
    'Manual review - LPI has no automation flow',
    1,
    CASE WHEN EXISTS (SELECT 1 FROM #SepReasonCodesNotAutomated WHERE ReasonCode = 'LPI') THEN 1 ELSE 0 END,
    CASE WHEN EXISTS (SELECT 1 FROM #SepReasonCodesNotAutomated WHERE ReasonCode = 'LPI') THEN 'PASS' ELSE 'FAIL' END;


/* =============================================================================
   SECTION 2b: Schema discovery - run this FIRST against your real database
   before touching Section 3, to confirm actual column names.
   ============================================================================= */

SELECT c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, c.CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_NAME IN ('tbtransactions', 'tbmemberinfo')
ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;

-- Sanity check: confirm the ElectionType column exists and see its actual
-- distinct values in your data (compare against the 22-code CMS table).
-- SELECT DISTINCT ElectionType FROM dbo.tbtransactions ORDER BY ElectionType;


/* =============================================================================
   SECTION 3: VALIDATION QUERY TEMPLATE - recalculates expected AEP/ICEP/IEP/
   SEPU effective dates for real transactions and flags mismatches against
   the stored value.

   *** Column names below marked --CONFIRM-- are ASSUMED, not verified ***
   Adjust them to match your Section 2b results before running.
   ============================================================================= */

SELECT
    t.TransactionId,                                  --CONFIRM-- PK column name
    t.ElectionType        AS StoredElectionType,       --CONFIRM--
    t.ApplicationDate     AS AppDate,                  --CONFIRM--
    t.EffectiveDate        AS StoredEffectiveDate,      --CONFIRM--
    m.DOB,                                             --CONFIRM-- from tbmemberinfo

    -- Recalculated AEP effective date, only meaningful when in-window
    dbo.fn_AepEffectiveDate(t.ApplicationDate) AS Recalc_AEP_EffectiveDate,

    -- Recalculated IEP effective date (requires DOB)
    dbo.fn_IepEffectiveDate(t.ApplicationDate, m.DOB) AS Recalc_IEP_EffectiveDate,

    -- Recalculated SEPU effective date
    dbo.fn_SepuEffectiveDate(t.ApplicationDate) AS Recalc_SEPU_EffectiveDate,

    CASE
        WHEN t.ElectionType = 'AEP'
             AND t.EffectiveDate <> dbo.fn_AepEffectiveDate(t.ApplicationDate)
        THEN 'MISMATCH: AEP effective date'

        WHEN t.ElectionType = 'IEP'
             AND t.EffectiveDate <> dbo.fn_IepEffectiveDate(t.ApplicationDate, m.DOB)
        THEN 'MISMATCH: IEP effective date'

        WHEN t.ElectionType = 'SEPU'
             AND t.EffectiveDate <> dbo.fn_SepuEffectiveDate(t.ApplicationDate)
        THEN 'MISMATCH: SEPU effective date'

        WHEN t.ElectionType = 'AEP' AND dbo.fn_IsAepWindow(t.ApplicationDate) = 0
        THEN 'FLAG: ElectionType=AEP but ApplicationDate outside Oct15-Dec7 window'

        ELSE 'OK / not checked by this template'
    END AS ValidationResult

FROM dbo.tbtransactions t                              --CONFIRM-- table/schema
LEFT JOIN dbo.tbmemberinfo m                            --CONFIRM-- table/schema
       ON m.MemberId = t.MemberId                       --CONFIRM-- join column(s)
WHERE t.ElectionType IN ('AEP', 'IEP', 'SEPU')          -- extend as more functions are added
  AND t.TransCode IN ('61')                             --CONFIRM-- restrict to relevant TC per doc
ORDER BY t.ApplicationDate DESC;


/* =============================================================================
   NEXT STEPS
   ============================================================================= */
-- 1. Run Section 2b against your DB, fix every --CONFIRM-- column/table name.
-- 2. Run Section 2 self-tests in a scratch DB (any SQL Server works - the
--    functions don't touch real tables) to confirm the T-SQL matches the
--    doc's worked examples, same as the Python version already validated.
-- 3. Run Section 3 against a small date-bounded slice of a TEST/UAT
--    environment first, not production, and review ValidationResult output
--    before trusting it at scale.
-- 4. Extend Section 3 with SEPV/SEPW/ICEP/SEPL/SEPQ checks once you've
--    confirmed where DOB, Part A/B/D entitlement dates, and move/release
--    dates live in your schema (likely tbmemberinfo or a related table
--    not named in the documentation provided).
