import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import os
import glob
import json
import matplotlib.pyplot as plt

# --- SİHİRLİ DOKUNUŞ: GÜÇLENDİRİLMİŞ YAKALAYICI ---
def web_show(*args, **kwargs):
    fig = plt.gcf()
    
    # Eğer hafızada çizilecek bir grafik yoksa boşuna işlem yapma
    if not fig.get_axes():
        return
        
    # Streamlit'in karanlık tema rengini zorla uyguluyoruz
    fig.patch.set_facecolor('#0e1117') 
    ax = plt.gca()
    ax.set_facecolor('#0e1117')
    
    # Yazıları görünür yap
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    
    # Açıklama (Legend) kutusunu koyulaştır
    legend = ax.get_legend()
    if legend:
        legend.get_frame().set_facecolor('#262730')
        legend.get_frame().set_edgecolor('#444444')
        for text in legend.get_texts():
            text.set_color("white")
            
    # Temizlenmiş grafiği çiz ve hafızayı boşalt
    st.pyplot(fig, use_container_width=False)
    plt.clf() 

plt.show = web_show

# Senin yazdığın modülleri içe aktarıyoruz
import Analizler
import BuzagiDurumTahminiMetotlar

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Buzağı İzleme Sistemi", page_icon="🐄", layout="wide")

# --- 2. VERİ YÜKLEME ---
@st.cache_data
def verileri_yukle(klasor_yolu="calfData_b435_d220319"):
    json_dosyalari = glob.glob(os.path.join(klasor_yolu, "*.json"))
    tum_ziyaret_sozlugu = {}

    for dosya in json_dosyalari:
        with open(dosya, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                veri = json.load(f)
            except:
                continue

            kuepe_no = veri.get("calfTitle", "Bilinmiyor")
            calf_code = veri.get("calfCode", "")
            cinsiyet = veri.get("calfGender", "X")
            benzersiz_kimlik = f"{kuepe_no}-{calf_code}" if calf_code else kuepe_no

            if "calfStatistic" in veri and len(veri["calfStatistic"]) > 0:
                for stat in veri["calfStatistic"]:
                    if "visits" in stat:
                        for visit in stat["visits"]:
                            tarih = visit.get("date", "Tarih Yok")
                            if "data" in visit:
                                for detay in visit["data"]:
                                    satir = {
                                        "Buzagi_ID": benzersiz_kimlik,
                                        "Gercek_Kuepe_No": kuepe_no,
                                        "calfCode": calf_code,
                                        "Cinsiyet": cinsiyet,
                                        "Tarih": tarih,
                                        "Saat": detay.get("hour"),
                                        "Hak_Ettigi_Sut_ml": detay.get("claim", 0),
                                        "Ictigi_Sut_ml": detay.get("consumption", 0),
                                        "Vakum_Suresi_sn": detay.get("vacuumTime", 0),
                                        "Iceride_Kalma_sn": detay.get("passingTime", 0),
                                        "Emzik_Vurma_Diaphragm": detay.get("diaphragm", 0),
                                        "Icme_Hizi": detay.get("averageSpeed", 0)
                                    }
                                    anahtar = (benzersiz_kimlik, tarih, detay.get("hour"))
                                    tum_ziyaret_sozlugu[anahtar] = satir

    df = pd.DataFrame(list(tum_ziyaret_sozlugu.values()))
    if not df.empty:
        df['Tarih_Saat'] = pd.to_datetime(df['Tarih'] + ' ' + df['Saat'], errors='coerce')
    return df

with st.spinner("Veri seti yükleniyor ve işleniyor..."):
    df = verileri_yukle()
    buzagi_listesi = df['Buzagi_ID'].unique().tolist() if not df.empty else []

# --- 3. YAN MENÜ ---
with st.sidebar:
    st.title("🐄 Kontrol Merkezi")
    st.markdown("---")
    
    secili_sayfa = option_menu(
        menu_title=None,
        options=[
            "Dashboard", "LSTM Tahmin", "Regresyon Grafiği", 
            "Veri Aktarımı (Excel)", "Sürü Stres Analizi", "Stres Grafikleri"
        ],
        icons=["grid-fill", "cpu", "graph-up", "file-earmark-excel", "activity", "reception-4"],
        default_index=0,
    )
    st.markdown("---")
    st.info("Sistem Durumu: Aktif 🟢")

# --- 4. PANEL İÇERİKLERİ ---

if secili_sayfa == "Dashboard":
    st.header("Veri Seti Genel Özeti")
    st.markdown("---")
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam İşlenen Veri", f"{len(df):,} Satır")
        col2.metric("Takip Edilen Buzağı", f"{len(buzagi_listesi)}")
        toplam_hak = df['Hak_Ettigi_Sut_ml'].sum()
        toplam_icilen = df['Ictigi_Sut_ml'].sum()
        basari_orani = (toplam_icilen / toplam_hak * 100) if toplam_hak > 0 else 0
        col3.metric("Sürü Süt Tüketim Başarısı", f"%{basari_orani:.1f}")
        st.dataframe(df.head(100), use_container_width=True)
    else:
        st.error("Veri seti yüklenemedi.")

elif secili_sayfa == "LSTM Tahmin":
    st.header("🧠 Yapay Zeka (LSTM) ile Gelecek Tahmini")
    secilen_buzagi = st.selectbox("Analiz Edilecek Buzağıyı Seçin:", buzagi_listesi)
    if st.button("Modeli Eğit ve Tahmin Et", type="primary"):
        with st.status("Yapay Zeka Çalışıyor...", expanded=True) as durum:
            st.write(f"{secilen_buzagi} için veriler hazırlanıyor...")
            BuzagiDurumTahminiMetotlar.buzagi_gelecek_sut_tahmini(df, secilen_buzagi)
            web_show() # Güvenlik Ağı!
            durum.update(label="Tahmin Tamamlandı!", state="complete", expanded=False)

elif secili_sayfa == "Regresyon Grafiği":
    st.header("📈 Sürü Meşguliyet Tahmini (Regresyon)")
    if st.button("Regresyon Analizini Başlat", type="primary"):
        with st.spinner("Model eğitiliyor ve grafik çiziliyor..."):
            Analizler.suru_mesguliyet_tahmini_regresyon(df)
            web_show() # Güvenlik Ağı!

elif secili_sayfa == "Sürü Stres Analizi":
    st.header("📋 Sürü Stres Analizi")
    if st.button("Analizi Başlat ve Excel'e Kaydet"):
        with st.spinner("Hesaplanıyor..."):
            Analizler.suru_stres_siralamasi_excel(df)
            st.success("İşlem Başarılı! 'Suru_Stres_Analizi_Kod_Bazli.xlsx' dosyası proje klasörüne kaydedildi.")

elif secili_sayfa == "Veri Aktarımı (Excel)":
    st.header("💾 Tüm Ham Verileri Excel'e Aktar")
    if st.button("Verileri Birleştir ve Çıkar"):
        with st.spinner("Veriler işleniyor..."):
            Analizler.ham_verileri_excele_aktar("calfData_b435_d220319")
            st.success("İşlem Başarılı! 'Tum_Ham_Veriler.xlsx' dosyası oluşturuldu.")

elif secili_sayfa == "Stres Grafikleri":
    st.header("📊 Bireysel Stres Grafiği")
    secilen_buzagi = st.selectbox("Grafiği Çizilecek Buzağıyı Seçin:", buzagi_listesi)
    if st.button("Grafiği Çiz", type="primary"):
        with st.spinner("Grafik hazırlanıyor..."):
            Analizler.stres_grafigi_ciz(df, secilen_buzagi)
            web_show() # Güvenlik Ağı!