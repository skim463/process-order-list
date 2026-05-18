import io
import csv
from collections import defaultdict

import pdfplumber
import streamlit as st


def extract_parts(pdf_file) -> dict:
    parts = defaultdict(lambda: {"qty": 0, "designation": "", "supplier": "", "part_number": ""})

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table or len(table) < 2:
                    continue
                header = table[0]
                if not any(str(c) in ("Typnummer", "Typenummer") for c in header if c):
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
                        entry["supplier"] = ((row[4] if len(row) > 4 else "") or "").strip()
                    if not entry["part_number"]:
                        entry["part_number"] = ((row[5] if len(row) > 5 else "") or "").strip()

    return parts


def to_csv_bytes(parts: dict) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Typnummer", "Quantity", "Designation", "Supplier", "Part number"])
    for typnummer, data in sorted(parts.items()):
        writer.writerow([typnummer, data["qty"], data["designation"], data["supplier"], data["part_number"]])
    return buffer.getvalue().encode("utf-8-sig")


# --- Page config ---
st.set_page_config(page_title="Parts List Aggregator", page_icon="⚙️", layout="centered")

st.title("⚙️ Parts List Aggregator")
st.write("Upload a **Parts List** `.pdf` file to extract and aggregate quantities by type number.")

uploaded_file = st.file_uploader("", type=["pdf"])

if uploaded_file:
    with st.spinner("Reading PDF..."):
        parts = extract_parts(uploaded_file)

    if not parts:
        st.error("No parts list table found in this PDF. Make sure it contains a 'Typnummer' column.")
    else:
        import pandas as pd
        df = pd.DataFrame([
            {
                "Typnummer": typ,
                "Quantity": data["qty"],
                "Designation": data["designation"],
                "Supplier": data["supplier"],
                "Part number": data["part_number"],
            }
            for typ, data in sorted(parts.items())
        ])

        csv_bytes = to_csv_bytes(parts)
        filename = uploaded_file.name.replace(".pdf", "_aggregated.csv")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"Found **{len(parts)} unique part types** across all pages.")
        with col2:
            st.download_button(
                label="Download CSV",
                data=csv_bytes,
                file_name=filename,
                mime="text/csv",
                use_container_width=True,
            )

        st.dataframe(df, use_container_width=True, hide_index=True)
