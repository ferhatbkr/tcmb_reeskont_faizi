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
        tarih = pd.to_datetime(
            str(row["tarih"]).strip(),
            format="%d.%m.%Y"
        )
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

    baslangic_yili = 2026
    bugun = pd.Timestamp.today().normalize()

    esas_rows = []

    for yil in range(baslangic_yili, bugun.year + 1):
        for ay in (1, 7):
            # Kanuni faiz dönemi hedef tarihi:
            # 1 Ocak veya 1 Temmuz
            hedef = pd.Timestamp(
                year=yil,
                month=ay,
                day=1
            )

            # Henüz gelmemiş dönemler oluşturulmasın.
            if hedef > bugun:
                continue

            # Hedef tarihten bir gün önceki tarih esas alınır.
            kontrol_tarihi = hedef - pd.Timedelta(days=1)

            # Kontrol tarihinden önce veya o gün yürürlükte olan
            # en yakın reeskont oranını bul.
            onceki = [
                (tarih, oran)
                for tarih, oran in rows
                if tarih <= kontrol_tarihi
            ]

            if not onceki:
                continue

            _, oran = onceki[-1]

            esas_rows.append(
                f"{hedef:%Y-%m-%d}|{oran:g}"
            )

    return "\n".join(esas_rows) + (
        "\n" if esas_rows else ""
    )


def main():
    new_content = get_faizler()
    old_content = (
        OUTPUT.read_text(encoding="utf-8")
        if OUTPUT.exists()
        else ""
    )

    if new_content != old_content:
        OUTPUT.write_text(
            new_content,
            encoding="utf-8"
        )
        print("TCMB faiz verisi güncellendi.")
    else:
        print("TCMB faiz verisinde değişiklik yok.")

    esas_content = get_esas(new_content)
    old_esas = (
        ESAS_OUTPUT.read_text(encoding="utf-8")
        if ESAS_OUTPUT.exists()
        else ""
    )

    if esas_content != old_esas:
        ESAS_OUTPUT.write_text(
            esas_content,
            encoding="utf-8"
        )
        print("Kanuni faize esas reeskont verisi güncellendi.")
    else:
        print(
            "Kanuni faize esas reeskont verisinde değişiklik yok."
        )


if __name__ == "__main__":
    main()
