import pandas as pd
from pathlib import Path

URL = "https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Temel+Faaliyetler/Para+Politikasi/Reeskont+ve+Avans+Faiz+Oranlari"
OUTPUT = Path("faizler.txt")
ESAS_OUTPUT = Path("esas.txt")


def get_faizler():
    table = pd.read_html(URL, decimal=",", thousands=None)[0]
    table.columns = ["tarih", "reeskont", "avans"]
    table = table[table["tarih"] != "Yürürlük Tarihi"]

    rows = []
    for _, row in table.iterrows():
        tarih = pd.to_datetime(str(row["tarih"]).strip(), format="%d.%m.%Y")
        reeskont = row["reeskont"]
        rows.append(f"{tarih:%Y-%m-%d}|{reeskont}")

    return "\n".join(rows) + "\n"


def get_esas(faizler_content):
    rows = []

    for line in faizler_content.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue

        tarih_str, oran_str = line.split("|", 1)
        try:
            tarih = pd.Timestamp(tarih_str)
            oran = float(str(oran_str).replace(",", "."))
        except (ValueError, TypeError):
            continue

        rows.append((tarih, oran))

    if not rows:
        return ""

    rows.sort(key=lambda x: x[0])

    # Kanuni faize esas reeskont oranı her yıl 1 Ocak ve 1 Temmuz'da,
    # ilgili tarihten önceki son geçerli reeskont oranıdır.
    baslangic = pd.Timestamp("2026-01-01")
    son_yil = max(tarih.year for tarih, _ in rows)
    hedefler = []

    for yil in range(baslangic.year, son_yil + 1):
        for ay in (1, 7):
            hedef = pd.Timestamp(year=yil, month=ay, day=1)
            if hedef > pd.Timestamp("today") and yil > son_yil:
                continue
            hedefler.append(hedef)

    esas_rows = []
    for hedef in hedefler:
        onceki = [(tarih, oran) for tarih, oran in rows if tarih < hedef]
        if not onceki:
            continue
        _, oran = onceki[-1]
        esas_rows.append(f"{hedef:%Y-%m-%d}|{oran:g}")

    return "\n".join(esas_rows) + ("\n" if esas_rows else "")


def main():
    new_content = get_faizler()
    old_content = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""

    if new_content != old_content:
        OUTPUT.write_text(new_content, encoding="utf-8")
        print("TCMB faiz verisi güncellendi.")
    else:
        print("TCMB faiz verisinde değişiklik yok.")

    esas_content = get_esas(new_content)
    old_esas = ESAS_OUTPUT.read_text(encoding="utf-8") if ESAS_OUTPUT.exists() else ""

    if esas_content != old_esas:
        ESAS_OUTPUT.write_text(esas_content, encoding="utf-8")
        print("Kanuni faize esas reeskont verisi güncellendi.")
    else:
        print("Kanuni faize esas reeskont verisinde değişiklik yok.")


if __name__ == "__main__":
    main()
