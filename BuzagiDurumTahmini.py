# -*- coding: utf-8 -*-
"""Buzağıların süt içme alışkanlıklarındaki dalgalanmaları takip eden ve olası
iştah düşüşlerini önceden tahmin ederek erken teşhis imkanı sunan yapay zeka
tabanlı bir karar destek sistemidir."""
import pandas as pd
import glob
import os
import json
import Analizler
import BuzagiDurumTahminiMetotlar

# --- VERİ OKUMA ---
klasor_yolu = "calfData_b435_d220319"
json_dosyalari = glob.glob(os.path.join(klasor_yolu, "*.json"))
tum_ziyaretler = []

for dosya in json_dosyalari:
    with open(dosya, 'r', encoding='utf-8', errors='ignore') as f:
        try:
            veri = json.load(f)
            kuepe_no = veri.get("calfTitle", "Bilinmiyor")
            calf_code = veri.get("calfCode", "")
            # Kimlik Oluşturma
            benzersiz_kimlik = f"{kuepe_no}-{calf_code}" if calf_code else kuepe_no

            if "calfStatistic" in veri:
                for stat in veri["calfStatistic"]:
                    if "visits" in stat:
                        for visit in stat["visits"]:
                            tarih = visit.get("date", "Tarih Yok")
                            if "data" in visit:
                                for detay in visit["data"]:
                                    tum_ziyaretler.append({
                                        "Buzagi_ID": benzersiz_kimlik,
                                        "Tarih": tarih,
                                        "Saat": detay.get("hour"),
                                        "Hak_Ettigi_Sut_ml": detay.get("claim", 0), # Eksik olan buydu!
                                        "Ictigi_Sut_ml": detay.get("consumption", 0),
                                        "Vakum_Suresi_sn": detay.get("vacuumTime", 0),
                                        "Emzik_Vurma_Diaphragm": detay.get("diaphragm", 0),
                                        "Icme_Hizi": detay.get("averageSpeed", 0)
                                    })
        except:
            continue

df = pd.DataFrame(tum_ziyaretler)

# --- ANA PROGRAM ---
if not df.empty:
    print(f"\n[+] {len(df)} satır veri yüklendi.")
    arama_metni = input("Analiz edilecek Buzağı ID (Örn: TR0001): ").strip()

    # ---  ARAMA: İçinde geçiyorsa bulur ---
    eslesenler = [id for id in df['Buzagi_ID'].unique() if arama_metni in id]

    if eslesenler:
        hedef_buzagi = eslesenler[0]  # İlk eşleşen tam kimliği seçer (TR0001-1911)
        print(f"[*] Bulunan Tam Kimlik: {hedef_buzagi}")

        Analizler.buzagi_raporu(df, hedef_buzagi)
        Analizler.stres_grafigi_ciz(df, hedef_buzagi)

        # Yapay Zeka Analizi (LSTM)
        BuzagiDurumTahminiMetotlar.buzagi_gelecek_sut_tahmini(df, hedef_buzagi)

        print("\n[+] Tüm işlemler başarıyla tamamlandı.")
        input("Çıkmak için Enter'a basın...")
    else:
        print(f"\n[!] HATA: '{arama_metni}' ile eşleşen bir buzağı bulunamadı.")