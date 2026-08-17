import pandas as pd
from pathlib import Path

URL = "https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Temel+Faaliyetler/Para+Politikasi/Reeskont+ve+Avans+Faiz+Oranlari"
OUTPUT = Path("faizler.txt")

def get_faizler():
    table = pd.read_html(URL, decimal=",", thousands=None)[0]
    table.columns = ["tarih", "reeskont", "avans"]
    table = table[table["tarih"] != "Yürürlük Tarihi"]

    rows = []
    for _, row in table.iterrows():
        tarih = pd.to_datetime(str(row["tarih"]).strip(), format="%d.%m.%Y")
        avans = row["avans"]
        rows.append(f"{tarih:%Y-%m-%d}|{avans}")

    return "\n".join(rows) + "\n"

def main():
    new_content = get_faizler()
    old_content = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""

    if new_content == old_content:
        print("TCMB faiz verisinde değişiklik yok.")
        return

    OUTPUT.write_text(new_content, encoding="utf-8")
    print("TCMB faiz verisi güncellendi.")

if __name__ == "__main__":
    main()
