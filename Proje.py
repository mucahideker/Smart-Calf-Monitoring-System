# -*- coding: utf-8 -*-
import os
import glob
import json
import pandas as pd
import Analizler

# TABLOYA CEVIRIYORUZ
klasor_yolu = "calfData_b435_d220319"
json_dosyalari = glob.glob(os.path.join(klasor_yolu, "*.json"))

tum_ziyaret_sozlugu = {}

for dosya in json_dosyalari:
    with open(dosya, 'r', encoding='utf-8', errors='ignore') as f:
        try:
            veri = json.load(f)
        except:
            continue

        # 1. Ham verileri cekiyoruz
        kuepe_no = veri.get("calfTitle", "Bilinmiyor")
        calf_code = veri.get("calfCode", "")
        cinsiyet = veri.get("calfGender", "X")

        # 2. Benzersiz Kimlik Olusturma
        benzersiz_kimlik = f"{kuepe_no}-{calf_code}" if calf_code else kuepe_no

        if "calfStatistic" in veri and len(veri["calfStatistic"]) > 0:
            for stat in veri["calfStatistic"]:
                if "visits" in stat:
                    for visit in stat["visits"]:
                        tarih = visit.get("date", "Tarih Yok")
                        
                        
                        
                        total_bilgisi = visit.get("total", {})
                        gunluk_kilo = total_bilgisi.get("weight", 0)
                        gunluk_hiz = total_bilgisi.get("averageSpeed", 0)
                        
                        # ------------------------------------------------------

                        if "data" in visit:
                            for detay in visit["data"]:
                                saat = detay.get("hour")

                                # satir verisini olustururken artik benzersiz kimligi ID yapiyoruz
                                satir = {
                                    "Buzagi_ID": benzersiz_kimlik,  # Analiz fonksiyonun buraya bakacak
                                    "Gercek_Kuepe_No": kuepe_no,  # Gerektiginde Excelde filtrelemek icin
                                    "calfCode": calf_code,
                                    "Cinsiyet": cinsiyet,
                                    "Tarih": tarih,
                                    "Saat": saat,
                                    "Hak_Ettigi_Sut_ml": detay.get("claim", 0),
                                    "Ictigi_Sut_ml": detay.get("consumption", 0),
                                    "Vakum_Suresi_sn": detay.get("vacuumTime", 0),
                                    "Iceride_Kalma_sn": detay.get("passingTime", 0),
                                    "Emzik_Vurma_Diaphragm": detay.get("diaphragm", 0),
                                    "Icme_Hizi": detay.get("averageSpeed", gunluk_hiz),
                                    "Kilo": detay.get("weight", gunluk_kilo)
                                    
                                }

                                anahtar = (benzersiz_kimlik, tarih, saat)
                                tum_ziyaret_sozlugu[anahtar] = satir

# dataframe donusturme
df = pd.DataFrame(list(tum_ziyaret_sozlugu.values()))

# Tarih ve Saat birlestirme
if not df.empty:
    df['Tarih_Saat'] = pd.to_datetime(df['Tarih'] + ' ' + df['Saat'], errors='coerce')

print(f"Toplam {len(df)} benzersiz satirlik veri tablosu hazirlandi!\n")

# ANALIZINI ISTEDIGIMIZ BUZAGININ TAGINI BURAYA GIRIYORUZ

# --- BURADAN İTİBAREN YENİ KOD BAŞLIYOR ---

if not df.empty:
    # Mevcut Buzağıların sadece ID ve Cinsiyetini Tablo Halinde Gösterir
    mevcut_buzagilar = df[['Buzagi_ID', 'Cinsiyet']].drop_duplicates().sort_values(by='Buzagi_ID')

    print("\n" + "=" * 40)
    print("--- SİSTEMDE KAYITLI BUZAĞI LİSTESİ ---")
    print("=" * 40)
    # head(20) diyerek ilk 20 tanesini gösteriyoruz ki terminal çok dolmasın
    print(mevcut_buzagilar.head(20).to_string(index=False))
    print("..." if len(mevcut_buzagilar) > 20 else "")
    print(f"Toplam {len(mevcut_buzagilar)} farklı buzağı bulundu.")
    print("=" * 40 + "\n")

    # buzağı seçim
    secilen_id = input("Analiz etmek istediğiniz Buzağı ID'sini girin (Örn: TR0001-1911): ").strip()

    if secilen_id in df['Buzagi_ID'].values:
        hedef_buzagi = secilen_id

        Analizler.buzagi_raporu(df, hedef_buzagi)
        Analizler.sabirsizlik_analizi(df, hedef_buzagi)
        Analizler.stres_grafigi_ciz(df, hedef_buzagi)

        print("\n[*] Sürü genel raporları hazırlanıyor...")
        #Analizler.suru_stres_siralamasi_excel(df)
        #Analizler.ham_verileri_excele_aktar("calfData_b435_d220319")
        Analizler.suru_mesguliyet_tahmini_regresyon(df)

        print("\n[+] Tüm işlemler başarıyla tamamlandı.")

    else:
        print(f"\n[!] HATA: '{secilen_id}' listede bulunamadı. Lütfen tam ID'yi doğru yazdığınızdan emin olun.")