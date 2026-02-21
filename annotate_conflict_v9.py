import csv

INPUT = r"C:\Users\ahk79\Downloads\msp_extractor_modular\validation_sheets_v9\validate_conflict.csv"
OUTPUT = INPUT  # overwrite in place

# Annotations keyed by row id (string, as read from CSV)
annotations = {
    "1": {
        "is_correct": "y",
        "is_relevant": "y",
        "error_type": "",
        "notes": "Spatial overlap of MPAs vs ISRAs - two competing marine conservation designations"
    },
    "2": {
        "is_correct": "y",
        "is_relevant": "y",
        "error_type": "",
        "notes": "Spatial overlap of ISRAs vs no-take MPAs - competing marine spatial designations"
    },
    "3": {
        "is_correct": "y",
        "is_relevant": "y",
        "error_type": "",
        "notes": "Classic conservation vs fisheries management use-use conflict"
    },
    "4": {
        "is_correct": "y",
        "is_relevant": "y",
        "error_type": "",
        "notes": "Offshore wind farms vs trawling - two distinct marine spatial uses"
    },
    "5": {
        "is_correct": "n",
        "is_relevant": "y",
        "error_type": "false_positive",
        "notes": "Fisher-species interaction is ecological, not a use-use conflict between human activities"
    },
    "6": {
        "is_correct": "y",
        "is_relevant": "y",
        "error_type": "",
        "notes": "Oyster farming vs vessel traffic - two distinct marine uses"
    },
    "7": {
        "is_correct": "y",
        "is_relevant": "y",
        "error_type": "",
        "notes": "Trap fisheries vs maritime traffic - two distinct marine uses"
    },
    "8": {
        "is_correct": "y",
        "is_relevant": "y",
        "error_type": "",
        "notes": "Aquaculture vs tourism - two distinct marine/coastal uses"
    },
    "9": {
        "is_correct": "n",
        "is_relevant": "y",
        "error_type": "false_positive",
        "notes": "Rising sea levels vs aquaculture is an environmental impact, not a use-use conflict"
    },
    "10": {
        "is_correct": "n",
        "is_relevant": "y",
        "error_type": "false_positive",
        "notes": "Sea use activities vs ecological environment is use-vs-environment, not use-use conflict"
    },
    "11": {
        "is_correct": "n",
        "is_relevant": "y",
        "error_type": "false_positive",
        "notes": "Sea use activities vs water quality is use-vs-environment, not use-use conflict"
    },
    "12": {
        "is_correct": "y",
        "is_relevant": "y",
        "error_type": "",
        "notes": "Fisheries vs navigation - two distinct marine uses"
    },
    "13": {
        "is_correct": "n",
        "is_relevant": "y",
        "error_type": "false_positive",
        "notes": "Vague governance interaction; coastal communities is not a specific marine use, no concrete use-use conflict"
    },
    "14": {
        "is_correct": "y",
        "is_relevant": "y",
        "error_type": "",
        "notes": "Fishery vs nature conservation - classic use-use trade-off"
    },
}

# Read all rows
with open(INPUT, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# Apply annotations
for row in rows:
    rid = row["id"].strip()
    if rid in annotations:
        ann = annotations[rid]
        row["is_correct"] = ann["is_correct"]
        row["is_relevant"] = ann["is_relevant"]
        row["error_type"] = ann["error_type"]
        row["notes"] = ann["notes"]

# Write back with utf-8-sig
with open(OUTPUT, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# Summary
correct = sum(1 for r in rows if r["is_correct"] == "y")
incorrect = sum(1 for r in rows if r["is_correct"] == "n")
total = len(rows)
print(f"Annotated {total} rows: {correct} correct, {incorrect} incorrect")
print(f"Precision: {correct}/{total} = {correct/total:.3f}")
