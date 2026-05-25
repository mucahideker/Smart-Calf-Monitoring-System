import cv2
import json
import os
import numpy as np
from ultralytics import YOLO

# 1. Dosya Yollarını Tanımlıyoruz
JSON_YOLU = "data/farm_zones.json"
MODEL_YOLU = "runs/detect/buzagi_modelimiz/weights/best.pt"
TEST_FOTO_YOLU = r"dataset\CFR-0322-TR-15\006_mp4-0009_jpg.rf.419n46MAAGhPFkLszP8o.jpg"

def main():
    # 2. JSON Verisini ve YOLO Modelini Yüklüyoruz
    if not os.path.exists(JSON_YOLU):
        print(f" Hata: {JSON_YOLU} dosyası bulunamadı!")
        return

    with open(JSON_YOLU, "r", encoding="utf-8") as f:
        harita_verisi = json.load(f)

    if "kamera_1" not in harita_verisi:
        print(" Hata: JSON içinde 'kamera_1' profili bulunamadı!")
        return
    
    kamera_haritasi = harita_verisi["kamera_1"]
    
    # --- GÜVENLİ POLİGON YÜKLEME ---
    # .get() kullanıyoruz ki isimler eşleşmezse kod çökmesin
    yemlik_veri = kamera_haritasi.get("Yemlik")
    suluk_veri = kamera_haritasi.get("Suluk")
    dinlenme_veri = kamera_haritasi.get("dinlenme_alani")

    yemlik_poligonu = np.array(yemlik_veri, dtype=np.int32) if yemlik_veri else None
    suluk_poligonu = np.array(suluk_veri, dtype=np.int32) if suluk_veri else None
    dinlenme_poligonu = np.array(dinlenme_veri, dtype=np.int32) if dinlenme_veri else None

    # Modeli yüklüyoruz
    model = YOLO(MODEL_YOLU)

    # 3. Fotoğrafı Yükle ve YOLO ile Tahmin Et
    img = cv2.imread(TEST_FOTO_YOLU)
    if img is None:
        print(" Hata: Test fotoğrafı yüklenemedi!")
        return

    sonuclar = model.predict(source=TEST_FOTO_YOLU, conf=0.25)

    print("\n--- 📊 Davranış Analiz Sonuçları ---")
    
    yemlik_sayac = 0
    suluk_sayac = 0
    dinlenme_sayac = 0

    for sonuc in sonuclar:
        boxes = sonuc.boxes
        for box in boxes:
            # Sınır kutusu koordinatlarını al [x1, y1, x2, y2]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # --- MERKEZ NOKTASI HESAPLAMA (Tepeden Çekim İçin) ---
            merkez_x = int((x1 + x2) / 2)
            merkez_y = int((y1 + y2) / 2)
            hedef_nokta = (merkez_x, merkez_y)

            # Nokta poligonun içinde mi kontrolü
            yemlikte_mi = cv2.pointPolygonTest(yemlik_poligonu, hedef_nokta, False) >= 0 if yemlik_poligonu is not None else False
            sulukta_mi = cv2.pointPolygonTest(suluk_poligonu, hedef_nokta, False) >= 0 if suluk_poligonu is not None else False
            dinlenmede_mi = cv2.pointPolygonTest(dinlenme_poligonu, hedef_nokta, False) >= 0 if dinlenme_poligonu is not None else False

            # Durum tespiti ve renk atamaları
            if yemlikte_mi:
                durum = "Yemlikte"
                renk = (0, 255, 255) # Sarı
                yemlik_sayac += 1
            elif sulukta_mi:
                durum = "Sulukta"
                renk = (255, 0, 0) # Mavi
                suluk_sayac += 1
            elif dinlenmede_mi:
                durum = "Dinleniyor"
                renk = (0, 255, 0) # Yeşil
                dinlenme_sayac += 1
            else:
                durum = "Diger Alan"
                renk = (128, 128, 128) # Gri

            # Ekrana kutuyu çiz, hedefe (göbeğe) küçük kırmızı nokta koy ve yazıyı yaz
            cv2.rectangle(img, (x1, y1), (x2, y2), renk, 2)
            cv2.circle(img, hedef_nokta, 5, (0, 0, 255), -1) 
            cv2.putText(img, durum, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, renk, 2)

    # 4. İstatistikleri Ekrana ve Terminale Basıyoruz
    print(f"Yemlikteki Buzağı Sayısı: {yemlik_sayac}")
    print(f"Sulukteki Buzağı Sayısı: {suluk_sayac}")
    print(f"Dinlenme Alanındaki Buzağı Sayısı: {dinlenme_sayac}")

    # Çizilmiş poligonları da şeffaf olarak resme ekle
    if yemlik_poligonu is not None: cv2.polylines(img, [yemlik_poligonu], True, (0, 255, 255), 2)
    if suluk_poligonu is not None: cv2.polylines(img, [suluk_poligonu], True, (255, 0, 0), 2)
    if dinlenme_poligonu is not None: cv2.polylines(img, [dinlenme_poligonu], True, (0, 255, 0), 2)

    # Sonucu Kaydet
    kayit_yolu = "runs/detect/analiz_sonuc.jpg"
    cv2.imwrite(kayit_yolu, img)
    print(f"\n🚀 Analiz tamamlandı! Sonuç resmi '{kayit_yolu}' konumuna kaydedildi.")

if __name__ == "__main__":
    main()