"""
oec_folder_watch.py
====================
Watches C:/temp/input for new OEC files and converts each one to an EAF
tab-delimited file in C:/temp/output.

Usage
-----
    python oec_folder_watch.py                  # uses default paths
    python oec_folder_watch.py --input  D:/oec/in  --output D:/oec/out
    python oec_folder_watch.py --once           # process existing files then exit

Requirements
------------
    pip install watchdog

Layout references
-----------------
    Source : MAPD PCUG v19.2 (June 2026)  – Layout 3-9 TC 61, 600-byte fixed-width
    Target : EAF Layout Guide v26.1.03    – New EAF Layout, 222 tab-delimited fields
"""

import argparse
import csv
import logging
import os
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── optional watchdog import ─────────────────────────────────────────────────
try:
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
    from watchdog.observers import Observer
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("oec_watch")

# ─────────────────────────────────────────────────────────────────────────────
# OEC parser  (MAPD PCUG v19.2, Layout 3-9 – TC 61)
# ─────────────────────────────────────────────────────────────────────────────

def _s(record: str, start: int, size: int) -> str:
    """Extract a fixed-width field (1-based start)."""
    return record[start - 1 : start - 1 + size].strip()


@dataclass
class OECRecord:
    beneficiary_id:            str   # pos   1-12
    surname:                   str   # pos  13-24
    first_name:                str   # pos  25-31
    middle_initial:            str   # pos  32
    sex_code:                  str   # pos  33
    birth_date:                str   # pos  34-41  YYYYMMDD
    eghp_flag:                 str   # pos  42
    pbp_number:                str   # pos  43-45
    election_type:             str   # pos  46
    contract_id:               str   # pos  47-51
    application_date:          str   # pos  52-59  YYYYMMDD
    transaction_type:          str   # pos  60-61
    effective_date:            str   # pos  64-71  YYYYMMDD
    segment_id:                str   # pos  72-74
    esrd_override:             str   # pos  80
    premium_withhold:          str   # pos  81
    part_c_premium:            str   # pos  82-87
    creditable_coverage:       str   # pos  94
    uncovered_months:          str   # pos  95-97
    employer_subsidy:          str   # pos  98
    part_d_opt_out:            str   # pos  99
    sep_reason_code:           str   # pos 101-102
    secondary_rx_flag:         str   # pos 135
    secondary_rx_id:           str   # pos 136-155
    secondary_rx_group:        str   # pos 156-170
    plan_assigned_id:          str   # pos 210-224
    rx_bin:                    str   # pos 225-230
    rx_pcn:                    str   # pos 231-240
    rx_group:                  str   # pos 241-255
    rx_id:                     str   # pos 256-275
    sec_rx_bin:                str   # pos 276-281
    sec_rx_pcn:                str   # pos 282-291
    rel_agent:                 str   # pos 292
    rel_broker:                str   # pos 293
    rel_ship:                  str   # pos 294
    rel_auth_rep:              str   # pos 295
    rel_other:                 str   # pos 296
    rel_self:                  str   # pos 297
    rel_form_blank:            str   # pos 298
    national_producer_number:  str   # pos 299-308
    oec_indicator:             str   # pos 309
    oec_application_date:      str   # pos 310-317  YYYYMMDD UTC
    oec_application_number:    str   # pos 318-329  12-char hex
    beneficiary_phone:         str   # pos 330-339
    beneficiary_email:         str   # pos 340-413


def parse_oec_record(line: str) -> Optional[OECRecord]:
    """Return an OECRecord for TC 61 lines; None for header/trailer/other."""
    if len(line) < 61:
        return None
    if _s(line, 60, 2) != "61":
        return None
    return OECRecord(
        beneficiary_id           = _s(line,   1, 12),
        surname                  = _s(line,  13, 12),
        first_name               = _s(line,  25,  7),
        middle_initial           = _s(line,  32,  1),
        sex_code                 = _s(line,  33,  1),
        birth_date               = _s(line,  34,  8),
        eghp_flag                = _s(line,  42,  1),
        pbp_number               = _s(line,  43,  3),
        election_type            = _s(line,  46,  1),
        contract_id              = _s(line,  47,  5),
        application_date         = _s(line,  52,  8),
        transaction_type         = _s(line,  60,  2),
        effective_date           = _s(line,  64,  8),
        segment_id               = _s(line,  72,  3),
        esrd_override            = _s(line,  80,  1),
        premium_withhold         = _s(line,  81,  1),
        part_c_premium           = _s(line,  82,  6),
        creditable_coverage      = _s(line,  94,  1),
        uncovered_months         = _s(line,  95,  3),
        employer_subsidy         = _s(line,  98,  1),
        part_d_opt_out           = _s(line,  99,  1),
        sep_reason_code          = _s(line, 101,  2),
        secondary_rx_flag        = _s(line, 135,  1),
        secondary_rx_id          = _s(line, 136, 20),
        secondary_rx_group       = _s(line, 156, 15),
        plan_assigned_id         = _s(line, 210, 15),
        rx_bin                   = _s(line, 225,  6),
        rx_pcn                   = _s(line, 231, 10),
        rx_group                 = _s(line, 241, 15),
        rx_id                    = _s(line, 256, 20),
        sec_rx_bin               = _s(line, 276,  6),
        sec_rx_pcn               = _s(line, 282, 10),
        rel_agent                = _s(line, 292,  1),
        rel_broker               = _s(line, 293,  1),
        rel_ship                 = _s(line, 294,  1),
        rel_auth_rep             = _s(line, 295,  1),
        rel_other                = _s(line, 296,  1),
        rel_self                 = _s(line, 297,  1),
        rel_form_blank           = _s(line, 298,  1),
        national_producer_number = _s(line, 299, 10),
        oec_indicator            = _s(line, 309,  1),
        oec_application_date     = _s(line, 310,  8),
        oec_application_number   = _s(line, 318, 12),
        beneficiary_phone        = _s(line, 330, 10),
        beneficiary_email        = _s(line, 340, 74),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Conversion helpers
# ─────────────────────────────────────────────────────────────────────────────

def _yyyymmdd_to_mmddyyyy(d: str) -> str:
    d = d.strip()
    return (d[4:6] + d[6:8] + d[0:4]) if len(d) == 8 and d.isdigit() else ""


def _map_sex(v: str) -> str:
    return {"1": "M", "2": "F"}.get(v.strip(), "U")


def _yn(v: str) -> str:
    return {"Y": "Yes", "N": "No"}.get(v.strip().upper(), "")


def _election(v: str) -> str:
    return {"A": "AEP", "S": "SEP", "I": "IEP",
            "O": "OEP", "G": "OEPI", "N": "ICEP"}.get(v.strip().upper(), v.strip())


def _relationship(r: OECRecord) -> str:
    pairs = [
        (r.rel_agent,      "1"), (r.rel_broker,    "2"),
        (r.rel_ship,       "3"), (r.rel_auth_rep,  "4"),
        (r.rel_other,      "5"), (r.rel_self,      "6"),
        (r.rel_form_blank, "7"),
    ]
    return ",".join(code for flag, code in pairs if flag.upper() == "Y")


# ─────────────────────────────────────────────────────────────────────────────
# EAF 222-field headers  (EAF Layout Guide v26.1.03)
# ─────────────────────────────────────────────────────────────────────────────

EAF_HEADERS = [
    "ConfirmationNumber","SubmitDate","ContractID","PBPID","SegmentID",
    "MemberTitle","MemberFirstName","MemberMiddleInitial","MemberLastName","MemberBirthDate",
    "MemberGender","MemberAddress1","MemberAddress2","MemberAddress3","MemberCity",
    "MemberState","MemberZip","MemberPhone","MemberEmailAddress","MemberMBI",
    "ApplicationSSN","MailingAddress1","MailingAddress2","MailingAddress3","MailingCity",
    "MailingState","MailingZip","MedicarePartA","MedicarePartB","EmergencyContact",
    "EmergencyPhone","EmergencyRelationship","Field33_REMOVED","Field34_REMOVED","OtherCoverage",
    "OtherCoverageName","OtherCoverageID","LongTermFacility","LongTermName","LongTermAddress",
    "LongTermPhone","AuthorizedRepName","AuthorizedRepAddress","AuthorizedRepCity","AuthorizedRepState",
    "AuthorizedRepZip","AuthorizedRepPhone","AuthorizedRepRelationship","Language","ESRD",
    "StateMedicaid","WorkStatus","Field53_REMOVED","OtherCoverageGroup","AgentID",
    "SubmitTime","PartDSubAppInd","DeemedInd","SubsidyPercentage","DeemedReasonCode",
    "LISCopayLevelID","DeemedCoPayLevelID","PartDOptOut","SEPReasonCode","SEPCMSReasonCode",
    "Field66_REMOVED","EnrollmentPlanYear","MemberID","GroupNumber","SubGroupNumber",
    "ClassNumber","BillingProfileID","EffectiveDate","TransactionType","ApplicationSignDate",
    "CreditableCoverage","UncoveredMonths","ElectionType","MedicaidNumber","SalesLocation",
    "BankAccountType","BankAccountNumber","BankACHRoutingNumber","MedicalProductNumber","PharmacyProductNumber",
    "VisionProductNumber","DentalProductNumber","EGHPFlag","PriorCommercialOverride","EmployerSubsidyOverride",
    "SecondaryRxFlag","SecondaryRxID","SecondaryRxGroup","DisenrollmentReason","SecondaryRxBIN",
    "Plan1","Plan2","Plan3","Plan4","Plan5",
    "Plan6","Plan7","Plan8","Plan9","Plan10",
    "UniqueKey","SpanType","SpanValue","SpanStartDate","SpanEndDate",
    "TransLevelPlan1","TransLevelPlan2","TransLevelPlan3","TransLevelPlan4","TransLevelPlan5",
    "TransLevelPlan6","TransLevelPlan7","TransLevelPlan8","TransLevelPlan9","TransLevelPlan10",
    "PrimaryRxID","LISEffectiveDate","LISTermDate","SCCCode","NewToMedicare",
    "RecentlyMoved","RecentlyReturnedToUS","ExtraHelpForPremiums","ExtraHelpForDrug","NoMoreHelpForDrugs",
    "LongTermCareFacility","LeftPACEProgram","LostDrugCoverage","LeavingEmployerOrUnion","PharmacyAssistanceProgram",
    "PlanEndingContract","DisenrolledFromSNP","RecentlyChangedMedicaidDate","LeftMAPlan","PCPID",
    "IPAGroupID","SEPSReason","ApplicationType","PremiumWithholdOption","RxGroup",
    "RxBIN","RxPCN","SecondaryRxPCN","SalesDate","EmployerGroupNumber",
    "MedicarePartD","SecondPhone","PCPLastName","PCPFirstName","PCPEffDate",
    "PCPEndDate","PCPProviderID","ReleasedFromIncarceration","LawfulPresenceInUS","RFIReceiptDate",
    "MedicalOSB","DentalOSB","VisionOSB","OtherOSB","OnHoldStatus",
    "MedicaidLevel","OnHoldReason","IsMAOEP","EnrollMedicareDate","IsEmergency",
    "DupeEditOvr","DateEditOvr","SpouseWorkStatus","AccessibilityFormat","EmailOptIn",
    "Race","Ethnicity","PreferredFirstName","PreferredLastName","PreferredPronoun",
    "GenderIdentity","NonBinaryGender","MemberAddressStartDate","MailingCountryCode","DifferentGenderIdentity",
    "SelfIdentify","DifferentSelfIdentify","IndividualRepName","RelationshipToEnrollee","NationalProducerNumber",
    "MPPPAction","MPPPTerminationReasonCode","MPPPTerminationDate",
    "ReservedFutureUse12","ReservedFutureUse13","ReservedFutureUse14","ReservedFutureUse15",
    "ReservedFutureUse16","ReservedFutureUse17","ReservedFutureUse18","ReservedFutureUse19",
    "ReservedFutureUse20","ReservedFutureUse21","ReservedFutureUse22","ReservedFutureUse23",
    "ReservedFutureUse24","ReservedFutureUse25","ReservedFutureUse26","ReservedFutureUse27",
    "ReservedFutureUse28","ReservedFutureUse29","ReservedFutureUse30","ReservedFutureUse31",
    "ReservedFutureUse32","ReservedFutureUse33","ReservedFutureUse34","ReservedFutureUse35",
    "ReservedFutureUse36","ReservedFutureUse37","ReservedFutureUse38","ReservedFutureUse39",
    "ReservedFutureUse40",
]

assert len(EAF_HEADERS) == 222


def build_eaf_row(r: OECRecord) -> list:
    row = [""] * 222
    row[0]   = r.oec_application_number[:12] if r.oec_indicator.upper() == "Y" else r.oec_application_number
    row[1]   = _yyyymmdd_to_mmddyyyy(r.oec_application_date)
    row[2]   = r.contract_id
    row[3]   = r.pbp_number.zfill(3)
    row[4]   = r.segment_id.zfill(3)
    row[6]   = r.first_name
    row[7]   = r.middle_initial
    row[8]   = r.surname
    row[9]   = _yyyymmdd_to_mmddyyyy(r.birth_date)
    row[10]  = _map_sex(r.sex_code)
    row[17]  = r.beneficiary_phone
    row[18]  = r.beneficiary_email
    row[19]  = r.beneficiary_id
    row[49]  = "Yes" if r.esrd_override.strip() not in ("", "0") else "No"
    row[62]  = _yn(r.part_d_opt_out)
    row[67]  = r.plan_assigned_id
    row[72]  = _yyyymmdd_to_mmddyyyy(r.effective_date)
    row[73]  = "61"
    row[74]  = _yyyymmdd_to_mmddyyyy(r.application_date)
    row[75]  = _yn(r.creditable_coverage)
    row[76]  = r.uncovered_months.zfill(3)
    row[77]  = _election(r.election_type)
    row[87]  = _yn(r.eghp_flag) if r.eghp_flag.strip() else "No"
    row[88]  = r.esrd_override
    row[89]  = _yn(r.employer_subsidy)
    row[90]  = "Yes" if (r.secondary_rx_flag.upper() == "Y" or r.sec_rx_bin.strip()) else "No"
    row[91]  = r.secondary_rx_id
    row[92]  = r.secondary_rx_group
    row[94]  = r.sec_rx_bin
    row[120] = r.rx_id
    row[142] = "4" if r.oec_indicator.upper() == "Y" else ""
    row[143] = r.premium_withhold
    row[144] = r.rx_group
    row[145] = r.rx_bin
    row[146] = r.rx_pcn
    row[147] = r.sec_rx_pcn
    row[188] = _relationship(r)
    row[189] = r.national_producer_number
    return row


# ─────────────────────────────────────────────────────────────────────────────
# Core file converter
# ─────────────────────────────────────────────────────────────────────────────

def convert_file(input_path: Path, output_path: Path) -> dict:
    """
    Convert one OEC file → EAF file.
    Returns a summary dict with keys: lines_read, records_written, skipped, oec_y.
    Raises on any file I/O error.
    """
    lines_read = records_written = skipped = oec_y = 0

    with (
        open(input_path,  "r", encoding="utf-8", errors="replace") as fin,
        open(output_path, "w", newline="", encoding="utf-8")       as fout,
    ):
        writer = csv.writer(fout, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(EAF_HEADERS)

        for raw in fin:
            line = raw.rstrip("\r\n")
            if not line:
                continue
            lines_read += 1
            rec = parse_oec_record(line)
            if rec is None:
                skipped += 1
                continue
            writer.writerow(build_eaf_row(rec))
            records_written += 1
            if rec.oec_indicator.upper() == "Y":
                oec_y += 1

    return dict(
        lines_read=lines_read,
        records_written=records_written,
        skipped=skipped,
        oec_y=oec_y,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Output filename builder
# ─────────────────────────────────────────────────────────────────────────────

def make_output_name(input_path: Path) -> str:
    """
    input : OEC_20260609.txt
    output: OEC_20260609_eaf_20260609_143012.txt
    """
    stem      = input_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stem}_eaf_{timestamp}.txt"


# ─────────────────────────────────────────────────────────────────────────────
# Process one file end-to-end (with done/ subfolder for processed originals)
# ─────────────────────────────────────────────────────────────────────────────

def process_file(input_path: Path, output_dir: Path) -> bool:
    """
    Convert input_path → output_dir/<name>_eaf_<ts>.txt
    Moves the original to input_path.parent/done/ on success.
    Returns True on success, False on error.
    """
    if not input_path.is_file():
        return False

    # Brief pause – give the OS time to finish writing the dropped file
    time.sleep(0.5)

    out_name   = make_output_name(input_path)
    out_path   = output_dir / out_name
    done_dir   = input_path.parent / "done"

    log.info("Processing  %s", input_path.name)
    try:
        summary = convert_file(input_path, out_path)
    except Exception as exc:
        log.error("FAILED  %s  →  %s", input_path.name, exc)
        return False

    log.info(
        "Done        %s  →  %s  "
        "(lines=%d  TC61=%d  OEC-Y=%d  skipped=%d)",
        input_path.name,
        out_path.name,
        summary["lines_read"],
        summary["records_written"],
        summary["oec_y"],
        summary["skipped"],
    )

    # Move original to done/
    done_dir.mkdir(exist_ok=True)
    dest = done_dir / input_path.name
    # Avoid collision if same name already exists
    if dest.exists():
        dest = done_dir / f"{input_path.stem}_{datetime.now().strftime('%H%M%S')}{input_path.suffix}"
    shutil.move(str(input_path), str(dest))
    log.info("Archived    %s  →  done/%s", input_path.name, dest.name)
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Process any files already sitting in the input folder on startup
# ─────────────────────────────────────────────────────────────────────────────

def process_existing(input_dir: Path, output_dir: Path) -> int:
    count = 0
    for f in sorted(input_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in (".txt", ".dat", ""):
            if process_file(f, output_dir):
                count += 1
    return count


# ─────────────────────────────────────────────────────────────────────────────
# Watchdog event handler
# ─────────────────────────────────────────────────────────────────────────────

if HAS_WATCHDOG:
    class OECHandler(FileSystemEventHandler):
        def __init__(self, input_dir: Path, output_dir: Path):
            self.input_dir  = input_dir
            self.output_dir = output_dir

        def on_created(self, event: FileCreatedEvent):
            if event.is_directory:
                return
            path = Path(event.src_path)
            if path.suffix.lower() not in (".txt", ".dat", ""):
                log.debug("Ignored (extension)  %s", path.name)
                return
            process_file(path, self.output_dir)


# ─────────────────────────────────────────────────────────────────────────────
# Fallback polling loop (no watchdog)
# ─────────────────────────────────────────────────────────────────────────────

def poll_loop(input_dir: Path, output_dir: Path, interval: int = 5):
    """
    Polls input_dir every `interval` seconds for new files.
    Tracks seen files so each is only processed once.
    """
    seen: set = set()
    log.info("Polling %s every %ds  (watchdog not installed)", input_dir, interval)
    while True:
        try:
            for f in sorted(input_dir.iterdir()):
                if f.is_file() and f.name not in seen and f.suffix.lower() in (".txt", ".dat", ""):
                    seen.add(f.name)
                    process_file(f, output_dir)
        except Exception as exc:
            log.warning("Poll error: %s", exc)
        time.sleep(interval)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_INPUT  = Path(r"C:/temp/input")
DEFAULT_OUTPUT = Path(r"C:/temp/output")


def main():
    parser = argparse.ArgumentParser(
        description="Watch a folder for OEC files and convert them to EAF."
    )
    parser.add_argument("--input",  type=Path, default=DEFAULT_INPUT,
                        help=f"Input folder to watch  (default: {DEFAULT_INPUT})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"Output folder for EAF files  (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--once",   action="store_true",
                        help="Process existing files then exit (no watching)")
    parser.add_argument("--poll",   type=int, default=5,
                        metavar="SECS",
                        help="Polling interval in seconds if watchdog is unavailable (default: 5)")
    args = parser.parse_args()

    input_dir:  Path = args.input
    output_dir: Path = args.output

    # Create folders if they don't exist
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("OEC → EAF folder converter  (MAPD PCUG v19.2 · EAF v26.1.03)")
    log.info("Input  : %s", input_dir.resolve())
    log.info("Output : %s", output_dir.resolve())

    # Add file handler so logs also go to output_dir/oec_converter.log
    log_file = output_dir / "oec_converter.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s",
                                       datefmt="%Y-%m-%d %H:%M:%S"))
    logging.getLogger().addHandler(fh)
    log.info("Log file   : %s", log_file)

    # Process anything already there
    n = process_existing(input_dir, output_dir)
    if n:
        log.info("Processed %d existing file(s) on startup.", n)

    if args.once:
        log.info("--once flag set, exiting.")
        return

    # Watch
    if HAS_WATCHDOG:
        log.info("Watching with watchdog (real-time)…  Press Ctrl+C to stop.")
        handler  = OECHandler(input_dir, output_dir)
        observer = Observer()
        observer.schedule(handler, str(input_dir), recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Stopping…")
            observer.stop()
        observer.join()
    else:
        log.warning("watchdog not installed – falling back to polling.")
        log.warning("Install it for instant detection:  pip install watchdog")
        try:
            poll_loop(input_dir, output_dir, interval=args.poll)
        except KeyboardInterrupt:
            log.info("Stopping.")


if __name__ == "__main__":
    main()
