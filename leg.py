from pathlib import Path
import pandas as pd

UPDATE_TYPE = "2"        # 1 = Reset Member file, 2 = Reset Transaction file
FILE_DATE   = "11212026" # MMDDYYYY: run date of the file you want cleared

# TransactionCode isn't in df yet; pull it from your source if you have it
if "TransactionCode" not in df.columns:
    df["TransactionCode"] = ""

out = pd.DataFrame({
    "MBI":      df["MBI"].fillna("").astype(str).str.strip(),
    "MemberID": df["MemberID"].fillna("").astype(str).str.strip(),
    "PlanID":   df["PlanID"].fillna("").astype(str).str.strip(),
    "PBPID":    df["PBPID"].fillna("").astype(str).str.strip().str.zfill(3),
    "TransCode":df["TransactionCode"].fillna("").astype(str).str.strip().str.zfill(2),
    "EffDate":  pd.to_datetime(df["EffectiveDate"], errors="coerce")
                  .dt.strftime("%m%d%Y").fillna(""),
    "UpdateType": UPDATE_TYPE,
    "FileDate":   FILE_DATE,
    "Err": df["FacetsErrorMessages"].fillna("").astype(str)
             .str.replace(r"[\r\n]+", " ", regex=True),
})

# UpdateType 1: transaction code / effective date don't apply
if UPDATE_TYPE == "1":
    out["TransCode"] = ""
    out["EffDate"] = ""

widths = {"MBI":15, "MemberID":15, "PlanID":5, "PBPID":3, "TransCode":2,
          "EffDate":8, "UpdateType":1, "FileDate":8, "Err":255}

def fixed(row):
    return "".join(str(row[c])[:w].ljust(w) for c, w in widths.items())

lines = out.apply(fixed, axis=1)
assert lines.str.len().eq(312).all()   # 15+15+5+3+2+8+1+8+255

outfile = Path(r"C:\apps\TC00\output") / "Legacy_Reset_Request.txt"
outfile.parent.mkdir(parents=True, exist_ok=True)
outfile.write_text("\n".join(lines) + "\n", encoding="ascii", errors="replace")
