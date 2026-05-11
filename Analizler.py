# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import os


def buzagi_raporu(df, buzagi_no):
    import pandas as pd

    ozel_df = df[df['Buzagi_ID'] == buzagi_no].copy()

    if ozel_df.empty:
        print(f"\n[!] HATA: {buzagi_no} numarali buzagi tabloda bulunamadi!")
        return

    ilk_kayit_sayisi = len(ozel_df)
    ozel_df = ozel_df.drop_duplicates(subset=['Tarih', 'Saat'], keep='first')
    silinen_kayit = ilk_kayit_sayisi - len(ozel_df)

    ozel_df['Hak_Ettigi_Sut_ml'] = pd.to_numeric(ozel_df['Hak_Ettigi_Sut_ml'], errors='coerce').fillna(0)
    ozel_df['Ictigi_Sut_ml'] = pd.to_numeric(ozel_df['Ictigi_Sut_ml'], errors='coerce').fillna(0)
    ozel_df['Vakum_Suresi_sn'] = pd.to_numeric(ozel_df['Vakum_Suresi_sn'], errors='coerce').fillna(0)

    print(f"\n=========================================")
    print(f" [ {buzagi_no} ] PERFORMANS RAPORU")
    print(f"=========================================")

    if silinen_kayit > 0:
        print(f" [*] Sistem Uyarisi: Tablodaki {silinen_kayit} adet mukerrer (kopya) log temizlendi.")

    if 'calfTotalConsumption' in ozel_df.columns:
        toplam_sut = ozel_df['calfTotalConsumption'].iloc[0]
    else:
        toplam_sut = ozel_df['Ictigi_Sut_ml'].sum()
        # ======================================================================

    sut_icen_df = ozel_df[ozel_df['Vakum_Suresi_sn'] > 0].copy()
    ort_hiz = 0
    if not sut_icen_df.empty:
        sut_icen_df['Icme_Hizi'] = sut_icen_df['Ictigi_Sut_ml'] / sut_icen_df['Vakum_Suresi_sn']
        ort_hiz = sut_icen_df['Icme_Hizi'].mean()

    print(f" Toplam Tuketim: {toplam_sut:,.0f} ml".replace(',', '.'))
    print(f" Ortalama Icme Hizi: {ort_hiz:.2f} ml/sn")

    istahsiz = ozel_df[(ozel_df['Hak_Ettigi_Sut_ml'] > 0) &
                       (ozel_df['Ictigi_Sut_ml'] < (ozel_df['Hak_Ettigi_Sut_ml'] * 0.5))]
    print(f" Yarim Birakilan Ogun: {len(istahsiz)} kez")

    odulsuz = ozel_df[(ozel_df['Hak_Ettigi_Sut_ml'] == 0) & (ozel_df['Ictigi_Sut_ml'] == 0)]
    toplam_ziyaret = len(ozel_df)
    stres_orani = (len(odulsuz) / toplam_ziyaret) * 100 if toplam_ziyaret > 0 else 0

    print(f" Odulsuz Ziyaret (Stres) Orani: %{stres_orani:.1f}")
    print("=========================================\n")


def stres_grafigi_ciz(df, buzagi_no):
    # guvenlik icin kopyala
    ozel_df = df[df['Buzagi_ID'] == buzagi_no].copy()

    if ozel_df.empty:
        print(f"\n[!] HATA: {buzagi_no} numarali buzagi tabloda bulunamadi!")
        return

    # tarihleri parcala
    ozel_df['Tarih'] = pd.to_datetime(ozel_df['Tarih'], format='%Y-%m-%d', errors='coerce')
    ozel_df = ozel_df.dropna(subset=['Tarih']).copy()

    # en az 2 gun  veri olmasi kontrol
    essiz_gun_sayisi = ozel_df['Tarih'].nunique()
    if essiz_gun_sayisi < 2:
        print(f"\n[!] UYARI: {buzagi_no} icin sadece {essiz_gun_sayisi} gunluk veri var.")
        print("    Cizgi grafigi olusturabilmek icin en az 2 farkli gune ait log gereklidir!")
        return

    ozel_df['Hak_Ettigi_Sut_ml'] = pd.to_numeric(ozel_df['Hak_Ettigi_Sut_ml'], errors='coerce').fillna(0)
    ozel_df['Ictigi_Sut_ml'] = pd.to_numeric(ozel_df['Ictigi_Sut_ml'], errors='coerce').fillna(0)

    # stres hesaplama
    stresli = ozel_df[(ozel_df['Hak_Ettigi_Sut_ml'] == 0) & (ozel_df['Ictigi_Sut_ml'] == 0)]
    stres_gunluk = stresli.groupby('Tarih').size()

    # bosluklari doldurma
    ilk_gun = ozel_df['Tarih'].min()
    son_gun = ozel_df['Tarih'].max()
    tum_takvim = pd.date_range(start=ilk_gun, end=son_gun)
    stres_gunluk = stres_gunluk.reindex(tum_takvim, fill_value=0)

    # 6. SADELESTIRILMIS GRAFIK CIZIMI
    plt.figure(figsize=(14, 6), facecolor='#f8f9fa')
    ax = plt.gca()
    ax.set_facecolor('#ffffff')

    # grafikte kirmizi cizdirme
    plt.plot(stres_gunluk.index, stres_gunluk.values,
             marker='o', color='#e63946', linewidth=2.5, markersize=6, label='Gunluk Bos Cikis (Stres)')

    # grafik cizdirme
    plt.fill_between(stres_gunluk.index, stres_gunluk.values, color='#e63946', alpha=0.1)

    # stres zirve noktasini bulup isaretleme
    if not stres_gunluk.empty and stres_gunluk.max() > 0:
        max_stres_degeri = stres_gunluk.max()
        max_stres_tarihi = stres_gunluk.idxmax()
        plt.annotate(f'Zirve Stres:\n{int(max_stres_degeri)} Kez',
                     xy=(max_stres_tarihi, max_stres_degeri),
                     xytext=(max_stres_tarihi, max_stres_degeri + (max_stres_degeri * 0.15)),
                     arrowprops=dict(facecolor='#1d3557', arrowstyle='wedge', alpha=0.8),
                     fontsize=10, fontweight='bold', color='#1d3557', ha='center')

    # basliklar etiketler
    plt.title(f"[{buzagi_no}] Hayvan Davranis Analizi: Gunluk Stres Grafigi", fontsize=15, fontweight='bold', pad=15)
    plt.xlabel("Beslenme Takvimi", fontsize=12, fontweight='bold', labelpad=10)
    plt.ylabel("Karsiliksiz Ziyaret", fontsize=12, fontweight='bold', labelpad=10)
    plt.grid(True, linestyle='--', alpha=0.4, which='major')

    # ================= tarih ekseni =================
    gun_sayisi = len(tum_takvim)
    # Eger takvim cok uzunsa (orn: 60 gun) tarihleri ust uste bindirmemek icin aralikli yazar
    if gun_sayisi > 30:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(gun_sayisi / 15)))
    else:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Az gun varsa her gunu yazar

    # Tarihleri dil bagimsiz, net GG-AA-YYYY formatina cevirir (Orn: 15-12-2024)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    plt.xticks(rotation=45, ha='right')
    # ========================================================================

    # Sag ve Ustteki cirkin cerceve cizgilerini kaldirma
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.legend(loc='upper right', frameon=True, shadow=True, fontsize=11)
    plt.tight_layout()
    plt.show()


def suru_stres_siralamasi_excel(df):
    liste = []

    for code in df['calfCode'].unique():
        # Belirli bir calfCode'a ait verileri filtrele
        o_df = df[df['calfCode'] == code]

        kuepe_no = o_df['Buzagi_ID'].iloc[0] if 'Buzagi_ID' in o_df.columns else "Bilinmiyor"

        toplam_giris = len(o_df)
        bos_cikis = len(o_df[(o_df['Hak_Ettigi_Sut_ml'] == 0) & (o_df['Ictigi_Sut_ml'] == 0)])

        # Stres orani hesaplama
        stres_orani = (bos_cikis / toplam_giris) * 100 if toplam_giris > 0 else 0

        liste.append({
            "Benzersiz_Kod": code,  # TR0001-1911 gibi olan kod
            "Kulak_Kupesi": kuepe_no,  # TR0001 gibi olan kupe no
            "Toplam_Giris": toplam_giris,
            "Sut_Icmeden_Cikis_Sayisi": bos_cikis,
            "Stres_Skoru_Yuzde": round(stres_orani, 2)
        })

    # Stres yuzdesine gore buyukten kucuge sirala
    sirali_df = pd.DataFrame(liste).sort_values(by="Stres_Skoru_Yuzde", ascending=False)

    dosya_adi = "Suru_Stres_Analizi_Kod_Bazli.xlsx"

    try:
        sirali_df.to_excel(dosya_adi, index=False)
        print(f"\n BASARILI: Analiz '{dosya_adi}' olarak kaydedildi!")
        print("Not: Buzagilar benzersiz 'calfCode' parametresine gore ayristirildi ve siralandi.")
    except Exception as e:
        print(f"\n Excel kaydedilemedi. Hata: {e}")


def sabirsizlik_analizi(df, buzagi_no):
    ozel_df = df[df['Buzagi_ID'] == buzagi_no].copy()
    if len(ozel_df) == 0: return

    # toplam ve ziyaret basina vurus
    toplam_vurus = ozel_df['Emzik_Vurma_Diaphragm'].sum()
    ziyaret_basina_vurus = toplam_vurus / len(ozel_df)

    # en agresif oldugu an tek seferde en fazla
    rekor_vurus_satiri = ozel_df.loc[ozel_df['Emzik_Vurma_Diaphragm'].idxmax()]
    rekor_vurus = rekor_vurus_satiri['Emzik_Vurma_Diaphragm']
    rekor_saat = rekor_vurus_satiri['Saat']
    rekor_tarih = rekor_vurus_satiri['Tarih']

    #  bos ziyaretlerdeki sabirsizlik
    bos_vurus = ozel_df[(ozel_df['Hak_Ettigi_Sut_ml'] == 0) &
                        (ozel_df['Ictigi_Sut_ml'] == 0)]['Emzik_Vurma_Diaphragm'].mean()

    print(f"\n--- {buzagi_no} SABIRSIZLIK VE AGRESIFLIK ANALIZI ---")
    print(f" Ziyaret Basina Ortalama Vurus: {ziyaret_basina_vurus:.2f}")
    print(f" Bos Dondugu Seanslardaki Agresiflik: {bos_vurus:.2f} vurus/seans")
    print(f" En Sinirli Oldugu An: {int(rekor_vurus)} vurus ile {rekor_tarih} {rekor_saat}")


def ham_verileri_excele_aktar(klasor_yolu, dosya_adi="Tum_Ham_Veriler.xlsx"):
    import os
    import glob
    import json
    import pandas as pd

    print(f"\n[*] Veriler isleniyor... Lutfen bekleyin.")
    json_dosyalari = glob.glob(os.path.join(klasor_yolu, "*.json"))
    tum_ziyaretler = []

    for dosya in json_dosyalari:
        with open(dosya, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                veri = json.load(f)
            except:
                continue

            calfTitle = veri.get("calfTitle", "Bilinmiyor")
            calfGender = veri.get("calfGender", "X")
            calfCode = veri.get("calfCode", "")
            calfTotalConsumption = veri.get("calfTotalConsumption", 0)
            calfFeedingStartDate = veri.get("calfFeedingStartDate", "")
            calfBirthDayDate = veri.get("calfBirthDayDate", "")
            calfFeedingDayCount = veri.get("calfFeedingDayCount", 0)

            medicine_history = ""
            calf_desc = veri.get("calfDesc", [])
            if calf_desc and len(calf_desc) > 0:
                desc_obj = calf_desc[0]
                medicines = desc_obj.get("medicine", [])
                med_list = []
                for med in medicines:
                    med_date = med.get("date", "")
                    med_name = med.get("name", "")
                    med_list.append(f"{med_date}: {med_name}")
                medicine_history = " | ".join(med_list)

            if "calfStatistic" in veri:
                for stat in veri["calfStatistic"]:
                    feedingType = stat.get("feedingType", "Bilinmiyor")
                    totalFeedingDay = stat.get("totalFeedingDay", 0)

                    if "visits" in stat:
                        for visit in stat["visits"]:
                            date = visit.get("date", "Tarih Yok")

                            total_info = visit.get("total", {})
                            gunluk_avg_speed = total_info.get("averageSpeed", 0)
                            gunluk_temp_boiler = total_info.get("tempBoiler", 0)
                            gunluk_claim = visit.get("claim", 0)
                            gunluk_weight = total_info.get("weight", 0)
                            gunluk_stop_count = total_info.get("consumptionStopCount", 0)
                            gunluk_speed_anomalies = total_info.get("speedAnomaliesCount", 0)

                            if "data" in visit and len(visit["data"]) > 0:
                                for detay in visit["data"]:
                                    satir = {
                                        "calfTitle": calfTitle,
                                        "calfCode": calfCode,
                                        "calfGender": calfGender,
                                        "calfBirthDayDate": calfBirthDayDate,
                                        "calfFeedingStartDate": calfFeedingStartDate,
                                        "calfFeedingDayCount": calfFeedingDayCount,
                                        "totalFeedingDay": totalFeedingDay,
                                        "calfTotalConsumption": calfTotalConsumption,
                                        "medicine": medicine_history,
                                        "feedingType": feedingType,
                                        "date": date,
                                        "hour": detay.get("hour"),
                                        "claim": detay.get("claim", 0),
                                        "consumption": detay.get("consumption", 0),
                                        "vacuumTime": detay.get("vacuumTime", 0),
                                        "passingTime": detay.get("passingTime", 0),
                                        "diaphragm": detay.get("diaphragm", 0),
                                        "weight": detay.get("weight", gunluk_weight),
                                        "consumptionStopCount": detay.get("consumptionStopCount", gunluk_stop_count),
                                        "speedAnomaliesCount": detay.get("speedAnomaliesCount", gunluk_speed_anomalies),
                                        "averageSpeed": detay.get("averageSpeed", gunluk_avg_speed),
                                        "tempBoiler": detay.get("tempBoiler", gunluk_temp_boiler)
                                    }
                                    tum_ziyaretler.append(satir)

                            else:
                                satir = {
                                    "calfTitle": calfTitle,
                                    "calfCode": calfCode,
                                    "calfGender": calfGender,
                                    "calfBirthDayDate": calfBirthDayDate,
                                    "calfFeedingStartDate": calfFeedingStartDate,
                                    "calfFeedingDayCount": calfFeedingDayCount,
                                    "totalFeedingDay": totalFeedingDay,
                                    "calfTotalConsumption": calfTotalConsumption,
                                    "medicine": medicine_history,
                                    "feedingType": feedingType,
                                    "date": date,
                                    "hour": "Gunluk_Ozet",
                                    "claim": gunluk_claim,
                                    "consumption": total_info.get("consumption", 0),
                                    "vacuumTime": total_info.get("vacuumTime", 0),
                                    "passingTime": total_info.get("passingTime", 0),
                                    "diaphragm": total_info.get("diaphragm", 0),
                                    "weight": gunluk_weight,
                                    "consumptionStopCount": gunluk_stop_count,
                                    "speedAnomaliesCount": gunluk_speed_anomalies,
                                    "averageSpeed": gunluk_avg_speed,
                                    "tempBoiler": gunluk_temp_boiler
                                }
                                tum_ziyaretler.append(satir)

    if not tum_ziyaretler:
        print("[!] Hata: Excel'e yazilacak veri bulunamadi.")
        return

    df = pd.DataFrame(tum_ziyaretler)

    df['sort_helper'] = df['calfTitle'].str.extract(r'(\d+)').astype(float)
    df = df.sort_values(by=["sort_helper", "date", "hour"])
    df = df.drop(columns=['sort_helper'])

    try:
        df.to_excel(dosya_adi, index=False)
        print(f"[+] BASARILI: '{dosya_adi}' olusturuldu.")
    except Exception as e:
        print(f"[!] Kayit hatasi: {e}")