import pdfplumber
import json
import os
import glob
from datetime import datetime

print("Starting cumulative PnL tracker...")
print("Script folder:", os.path.dirname(os.path.abspath(__file__)))

script_folder = os.path.dirname(os.path.abspath(__file__))
pdf_folder = script_folder

cumulative_file = os.path.join(script_folder, "cumulative_data.json")

# Safe load or initialize
cumulative = {
    "start_date": "2026-02-12",
    "start_pnl": 0.0,
    "daily_entries": []
}

if os.path.exists(cumulative_file):
    try:
        with open(cumulative_file, "r") as f:
            content = f.read().strip()
            if content:
                loaded = json.loads(content)
                cumulative.update(loaded)
                print("Loaded existing data")
            else:
                print("Empty JSON — starting fresh")
    except Exception as e:
        print("Error loading JSON:", e)
        print("Starting fresh")

processed = {entry.get("pdf_file", "") for entry in cumulative["daily_entries"]}

pdf_files = glob.glob(os.path.join(pdf_folder, "**", "*Performance*.pdf"), recursive=True)

print(f"Found {len(pdf_files)} PDF files:")
for f in pdf_files:
    print(" -", os.path.basename(f))

new_added = False

for pdf_path in sorted(pdf_files):
    pdf_name = os.path.basename(pdf_path)
    if pdf_name in processed:
        print(f"Already processed: {pdf_name}")
        continue

    print(f"\nProcessing: {pdf_name}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            all_tables = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                all_tables.extend(page.extract_tables())

        today = {
            "gross_pnl": 0.0,
            "fees": 0.0,
            "net_pnl": 0.0,
            "trades_count": 0,
            "win_rate": 0.0,
            "expectancy": 0.0,
            "max_runup": 0.0,
            "max_drawdown": 0.0,
            "trades": []
        }

        # Parse summary stats from text
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if "Gross P/L" in line:
                try:
                    val = float(line.split()[-1].replace(',', '').replace('$', ''))
                    today["gross_pnl"] = val
                except:
                    pass
            if "Trade Fees & Comm." in line:
                try:
                    val = float(line.split()[-1].replace(',', '').replace('$', '').replace('(', '-').replace(')', ''))
                    today["fees"] = val
                except:
                    pass
            if "Total P/L" in line:
                try:
                    val = float(line.split()[-1].replace(',', '').replace('$', ''))
                    today["net_pnl"] = val
                except:
                    pass
            if "% Profitable Trades" in line:
                try:
                    val = float(line.split()[-1].replace('%', ''))
                    today["win_rate"] = val
                except:
                    pass
            if "# of Trades" in line:
                try:
                    val = int(line.split()[-1])
                    today["trades_count"] = val
                except:
                    pass
            if "Expectancy" in line:
                try:
                    val = float(line.split()[-1].replace('$', ''))
                    today["expectancy"] = val
                except:
                    pass
            if "Max Run-up" in line:
                try:
                    val = float(line.split()[-1].replace(',', '').replace('$', ''))
                    today["max_runup"] = val
                except:
                    pass
            if "Max Drawdown" in line:
                try:
                    val = float(line.split()[-1].replace(',', '').replace('$', '').replace('(', '-').replace(')', ''))
                    today["max_drawdown"] = val
                except:
                    pass

        # Trades table - find the table with 9 rows (header + 8 trades)
        for table in all_tables:
            if len(table) == 9:  # your example has 9 rows
                print(f"  Found trades table with 8 trades")
                header = table[0]
                pnl_col = -1
                for i, h in enumerate(header):
                    if "p&l" in str(h).lower():
                        pnl_col = i
                        break
                if pnl_col == -1:
                    pnl_col = len(header) - 1

                for row in table[1:]:
                    if len(row) > pnl_col and row[pnl_col]:
                        pnl_str = str(row[pnl_col]).strip().replace(',', '').replace('$', '').replace('(', '-').replace(')', '')
                        try:
                            pnl_val = float(pnl_str)
                            today["trades"].append({
                                "symbol": row[0] if len(row) > 0 else "",
                                "qty": row[1] if len(row) > 1 else "",
                                "buy_price": row[2] if len(row) > 2 else "",
                                "buy_time": row[3] if len(row) > 3 else "",
                                "sell_price": row[6] if len(row) > 6 else "",
                                "pnl": pnl_val
                            })
                            print(f"  Added trade PnL: ${pnl_val:.2f}")
                        except:
                            pass

        # Prefer net from text if available
        if today["net_pnl"] != 0.0:
            today["pnl"] = today["net_pnl"]
        elif today["gross_pnl"] != 0.0:
            today["pnl"] = today["gross_pnl"] + today["fees"]

        if today["pnl"] == 0.0:
            print("  No PnL data found — skipping")
            continue

        # Date from filename
        try:
            date_part = pdf_name.split('.')[1]
            dt = datetime.strptime(date_part, "%Y%m%d")
            today["date"] = dt.strftime("%Y-%m-%d")
        except:
            today["date"] = datetime.now().strftime("%Y-%m-%d")

        # Cumulative
        last_cumulative = cumulative["daily_entries"][-1]["cumulative_pnl"] if cumulative["daily_entries"] else 0.0
        today["cumulative_pnl"] = round(last_cumulative + today["pnl"], 2)
        today["pdf_file"] = pdf_name

        cumulative["daily_entries"].append(today)
        new_added = True

        print(f"  Added {today['date']}: Daily PnL ${today['pnl']:.2f} | Cumulative ${today['cumulative_pnl']:.2f}")

    except Exception as e:
        print(f"  Error on {pdf_name}: {e}")

if new_added:
    with open(cumulative_file, "w") as f:
        json.dump(cumulative, f, indent=2)
    print("\nSuccess! cumulative_data.json updated with rich data.")
    print("Now open GitHub Desktop → Commit → Push")
else:
    print("\nNo new PDFs or no PnL found.")
    print("Folder checked:", pdf_folder)

input("\nPress Enter to close...")