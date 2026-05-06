import pdfplumber
import csv
from collections import defaultdict
from pathlib import Path


def extract_parts(pdf_path: str) -> dict:
    parts = defaultdict(lambda: {"qty": 0, "designation": "", "supplier": "", "part_number": ""})

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table or len(table) < 2:
                    continue
                header = table[0]
                if not any("Typnummer" in str(c) for c in header if c):
                    continue
                for row in table[1:]:
                    if not row or len(row) < 4:
                        continue
                    typnummer = (row[3] or "").strip()
                    if not typnummer or typnummer == "Typnummer":
                        continue
                    try:
                        qty = int((row[1] or "0").strip())
                    except ValueError:
                        qty = 0
                    entry = parts[typnummer]
                    entry["qty"] += qty
                    if not entry["designation"]:
                        entry["designation"] = (row[2] or "").strip()
                    if not entry["supplier"]:
                        entry["supplier"] = (row[4] if len(row) > 4 else "") or ""
                        entry["supplier"] = entry["supplier"].strip()
                    if not entry["part_number"]:
                        entry["part_number"] = (row[5] if len(row) > 5 else "") or ""
                        entry["part_number"] = entry["part_number"].strip()

    return parts


def write_csv(parts: dict, output_path: str) -> None:
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Typnummer", "Quantity", "Designation", "Supplier", "Part number"])
        for typnummer, data in sorted(parts.items()):
            writer.writerow([typnummer, data["qty"], data["designation"], data["supplier"], data["part_number"]])


def main():
    pdf_path = r"C:\Users\skim\DS project\process-order-list\E700 - Startercabinet 22kW (1).pdf"
    output_path = r"C:\Users\skim\DS project\process-order-list\parts_list_aggregated.csv"

    print(f"Reading: {pdf_path}")
    parts = extract_parts(pdf_path)

    write_csv(parts, output_path)
    print(f"Written {len(parts)} unique parts to: {output_path}")

    print(f"\n{'Typnummer':<30} {'Qty':>5}  Designation")
    print("-" * 80)
    for typnummer, data in sorted(parts.items()):
        print(f"{typnummer:<30} {data['qty']:>5}  {data['designation'][:40]}")


if __name__ == "__main__":
    main()
