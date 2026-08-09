import random
import string
import pandas as pd

input_path = "input/DTRR_file.txt"
output_path = "output/DTRR_file.txt"

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
# Read the file
# ------------------------------
with open(input_path, "r") as f:
    lines = [l.rstrip("\n") for l in f if l.strip()]

# ------------------------------
# Build a df holding the new values, one row per line in the file
# ------------------------------
df = pd.DataFrame({"original_line": lines})
df["new_mbi"] = [generate_mbi() for _ in range(len(df))]
df["new_last"] = [random.choice(last_names) for _ in range(len(df))]
df["new_first"] = [random.choice(first_names) for _ in range(len(df))]

# ------------------------------
# Apply the df values to override each line (bytes 0-30 only)
# ------------------------------
df["updated_line"] = df.apply(
    lambda r: r["new_mbi"].ljust(12) + r["new_last"].ljust(12) + r["new_first"].ljust(7) + r["original_line"][31:],
    axis=1,
)

with open(output_path, "w") as f:
    f.write("\n".join(df["updated_line"]) + "\n")

print(f"Overrode {len(df)} lines -> {output_path}")
