input_file = "input.txt"
rows_per_chunk = 10

with open(input_file, "r") as f:
    lines = f.readlines()

header = lines[0]
data_lines = lines[1:]

for i in range(0, len(data_lines), rows_per_chunk):
    chunk = data_lines[i:i + rows_per_chunk]
    out_name = f"part_{i // rows_per_chunk + 1}.txt"
    with open(out_name, "w") as out:
        out.write(header)
        out.writelines(chunk)

print(f"Split into {(len(data_lines) + rows_per_chunk - 1) // rows_per_chunk} files.")
