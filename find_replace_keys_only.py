import json

find = "FP"
replace = "PF"

source_file = "./es.json"

# Load file into JSON
with open(source_file, "r") as file:
    data = json.load(file)

# Find and replace in values only
for key in data:
    data[key] = data[key].replace(find, replace)

# Save back to json file ensure ascii
with open(source_file, "w") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)
