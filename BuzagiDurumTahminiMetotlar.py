# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout


def veri_hazirla_ve_olceklendir(ozel_df):
    kullanilacak_kolonlar = ['Ictigi_Sut_ml', 'Vakum_Suresi_sn', 'Emzik_Vurma_Diaphragm', 'Icme_Hizi']
    ozel_df = ozel_df.sort_values(by=['Tarih', 'Saat'])
    veri_matrisi = ozel_df[kullanilacak_kolonlar].values
    scaler = MinMaxScaler(feature_range=(0, 1))
    return scaler.fit_transform(veri_matrisi), scaler


def pencereli_veri_uret(veri, pencere_boyutu=5):
    X, y = [], []
    for i in range(len(veri) - pencere_boyutu):
        X.append(veri[i:(i + pencere_boyutu)])
        y.append(veri[i + pencere_boyutu, 0])
    return np.array(X), np.array(y)


def lstm_modeli_kur(pencere_boyutu, ozellik_sayisi):
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(pencere_boyutu, ozellik_sayisi)),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model


def buzagi_gelecek_sut_tahmini(df, buzagi_no, pencere_boyutu=5):
    ozel_df = df[df['Buzagi_ID'] == buzagi_no].copy()
    if len(ozel_df) < 15:
        print(f"\n[!] LSTM için yetersiz veri ({buzagi_no})")
        return

    olcekli_veri, scaler = veri_hazirla_ve_olceklendir(ozel_df)
    X, y = pencereli_veri_uret(olcekli_veri, pencere_boyutu)

    split = int(len(X) * 0.8)
    X_train, X_test, y_train, y_test = X[:split], X[split:], y[:split], y[split:]

    model = lstm_modeli_kur(pencere_boyutu, X.shape[2])
    print(f"\n[*] {buzagi_no} için yapay zeka eğitiliyor...")
    model.fit(X_train, y_train, epochs=20, batch_size=8, verbose=0)

    # --- TAHMİN VE GRAFİK FONKSİYONUN İÇİNDE ---
    print("[+] Model eğitildi, tahminler yapılıyor...")
    tahminler = model.predict(X_test)

    plt.figure(figsize=(12, 6), facecolor='#f0f0f0')
    plt.plot(y_test, color='blue', label='Gerçekleşen Tüketim (Ölçekli)', linewidth=2)
    plt.plot(tahminler, color='red', label='LSTM Gelecek Tahmini (Ölçekli)', linestyle='--', linewidth=2)

    plt.title(f"[{buzagi_no}] Yapay Zeka Beslenme Tahmin Analizi", fontsize=14)
    plt.xlabel("Sonraki Ziyaretler (Test Verisi)", fontsize=12)
    plt.ylabel("Süt Tüketim Oranı (0-1 Arası)", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)

    print("[*] Grafik açılıyor. Pencereyi kapatana kadar program bekleyecektir...")
    plt.show(block=True)