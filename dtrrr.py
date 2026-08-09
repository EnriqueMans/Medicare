import random
import string
import pandas as pd

input_path = "input/DTRR_file.txt"   # or your EAF file
output_path = "output/DTRR_file.txt"

# ------------------------------
# Just change these colspecs for whichever fixed-width file you're
# working with (DTRR, EAF, etc). (start, end) = byte offsets, 0-indexed,
# end-exclusive - same convention as pandas.read_fwf.
# ------------------------------
COLSPECS = [
    ("mbi", 0, 12),
    ("last_name", 12, 24),
    ("first_name", 24, 31),
]
colspecs = [(s, e) for _, s, e in COLSPECS]
names = [n for n, _, _ in COLSPECS]

first_names = ["JAMES", "MARY", "ROBERT", "PATRICIA", "JOHN", "JENNIFER", "MICHAEL", "LINDA"]
last_names = ["SMITH", "JOHNSON", "WILLIAMS", "BROWN", "JONES", "GARCIA", "MILLER", "DAVIS"]
alpha = "".join(c for c in string.ascii_uppercase if c not in "SLOIBZ")
alnum = string.digits + alpha


def generate_mbi():
    return (random.choice("123456789") + random.choice(alpha) + random.choice(alnum) +
            random.choice(string.digits) + random.choice(alpha) + random.choice(alnum) +
            random.choice(string.digits) + random.choice(string.digits) +
            random.choice(alpha) + random.choice(alpha) + random.choice(string.digits))


# ------------------------------
# Read the raw lines (kept so we can preserve everything past byte 31
# exactly as-is) and the parsed fixed-width columns
# ------------------------------
with open(input_path, "r") as f:
    raw_lines = [l.rstrip("\n") for l in f if l.strip()]

df = pd.read_fwf(input_path, colspecs=colspecs, names=names, dtype=str)
df["raw_line"] = raw_lines
df["remainder"] = df["raw_line"].str[colspecs[-1][1]:]  # everything after the last mapped field

# ------------------------------
# Generate new values (vectorized where possible)
# ------------------------------
df["mbi"] = [generate_mbi() for _ in range(len(df))]
df["last_name"] = pd.Series(last_names)[
    [random.randrange(len(last_names)) for _ in range(len(df))]
].values
df["first_name"] = pd.Series(first_names)[
    [random.randrange(len(first_names)) for _ in range(len(df))]
].values

# ------------------------------
# Rebuild each line: new fixed-width fields + untouched remainder
# ------------------------------
df["updated_line"] = (
    df["mbi"].str.ljust(12)
    + df["last_name"].str.ljust(12)
    + df["first_name"].str.ljust(7)
    + df["remainder"]
)

with open(output_path, "w") as f:
    f.write("\n".join(df["updated_line"]) + "\n")

print(f"Overrode {len(df)} lines -> {output_path}")
