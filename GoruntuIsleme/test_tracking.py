import cv2
import json
import os
import glob
import numpy as np
from ultralytics import YOLO

# 1. Dosya Yolları
JSON_YOLU = "data/farm_zones.json"
MODEL_YOLU = "runs/detect/buzagi_modelimiz/weights/best.pt"
# Fotoğrafların bulunduğu klasör yolu (Kendi yoluna göre güncelleyebilirsin)
KLASOR_YOLU = r"dataset\CFR-0322-TR-15" 

def main():
    # --- HARİTA YÜKLEME (Aynı Mantık) ---
    if not os.path.exists(JSON_YOLU):
        print(f"Hata: {JSON_YOLU} dosyası bulunamadı!")
        return

    with open(JSON_YOLU, "r", encoding="utf-8") as f:
        harita_verisi = json.load(f)

    kamera_haritasi = harita_verisi.get("kamera_1", {})
    yemlik_veri = kamera_haritasi.get("Yemlik")
    suluk_veri = kamera_haritasi.get("Suluk")
    dinlenme_veri = kamera_haritasi.get("dinlenme_alani")

    yemlik_poligonu = np.array(yemlik_veri, dtype=np.int32) if yemlik_veri else None
    suluk_poligonu = np.array(suluk_veri, dtype=np.int32) if suluk_veri else None
    dinlenme_poligonu = np.array(dinlenme_veri, dtype=np.int32) if dinlenme_veri else None

    # --- MODELİ YÜKLE ---
    model = YOLO(MODEL_YOLU)

    # --- KRONOLOJİK DOSYA OKUMA ---
    # Klasördeki "006_mp4" ile başlayan tüm JPG'leri bul ve isme göre sıraya diz
    arama_deseni = os.path.join(KLASOR_YOLU, "006_mp4-*.jpg")
    fotograflar = sorted(glob.glob(arama_deseni))

    if not fotograflar:
        print("Hata: Klasörde belirtilen şablona uyan fotoğraf bulunamadı!")
        return

    print(f"Toplam {len(fotograflar)} kare bulundu. Video simülasyonu ve Tracking başlıyor...")

    # --- TAKİP (TRACKING) DÖNGÜSÜ ---
    for img_yolu in fotograflar:
        frame = cv2.imread(img_yolu)
        if frame is None:
            continue

        # predict yerine track kullanıyoruz. persist=True modeli hafızalı yapar!
        # tracker="bytetrack.yaml" YOLO'nun içindeki en güçlü takip algoritmasıdır
        sonuclar = model.track(frame, persist=True, tracker="bytetrack.yaml", conf=0.25, verbose=False)

        # İlk (ve tek) sonucu al
        sonuc = sonuclar[0]
        
        # Eğer ekranda takip edilen bir nesne (ID) varsa işlemleri yap
        if sonuc.boxes.id is not None:
            # Kutuları ve ID'leri alıyoruz
            boxes = sonuc.boxes.xyxy.int().cpu().tolist()
            track_ids = sonuc.boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = box
                
                # Merkez hesaplama
                merkez_x = int((x1 + x2) / 2)
                merkez_y = int((y1 + y2) / 2)
                hedef_nokta = (merkez_x, merkez_y)

                # Bölge kontrolü
                yemlikte_mi = cv2.pointPolygonTest(yemlik_poligonu, hedef_nokta, False) >= 0 if yemlik_poligonu is not None else False
                sulukta_mi = cv2.pointPolygonTest(suluk_poligonu, hedef_nokta, False) >= 0 if suluk_poligonu is not None else False
                dinlenmede_mi = cv2.pointPolygonTest(dinlenme_poligonu, hedef_nokta, False) >= 0 if dinlenme_poligonu is not None else False

                if yemlikte_mi:
                    durum = "Yemlikte"
                    renk = (0, 255, 255) # Sarı
                elif sulukta_mi:
                    durum = "Sulukta"
                    renk = (255, 0, 0) # Mavi
                elif dinlenmede_mi:
                    durum = "Dinleniyor"
                    renk = (0, 255, 0) # Yeşil
                else:
                    durum = "Diger"
                    renk = (128, 128, 128) # Gri

                # Ekrana çizimler: Bu sefer başa ID ekliyoruz (Örn: "ID: 5 | Yemlikte")
                etiket = f"ID: {track_id} | {durum}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), renk, 2)
                cv2.circle(frame, hedef_nokta, 5, (0, 0, 255), -1) 
                cv2.putText(frame, etiket, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, renk, 2)

        # Poligonları çiz
        if yemlik_poligonu is not None: cv2.polylines(frame, [yemlik_poligonu], True, (0, 255, 255), 2)
        if suluk_poligonu is not None: cv2.polylines(frame, [suluk_poligonu], True, (255, 0, 0), 2)
        if dinlenme_poligonu is not None: cv2.polylines(frame, [dinlenme_poligonu], True, (0, 255, 0), 2)

        # Çıktıyı ekranda bir video gibi göster
        MAX_GENISLIK = 1280
        h, w = frame.shape[:2]
        if w > MAX_GENISLIK:
            oran = MAX_GENISLIK / w
            kucultulmus_frame = cv2.resize(frame, (int(w * oran), int(h * oran)))
            cv2.imshow("Frameleri videoya cevirme - Tracking", kucultulmus_frame)
        else:
            cv2.imshow("Frameleri videoya cevirme - Tracking", frame)

        # 'q' tuşuna basarak simülasyonu durdurabilirsin
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    print("Tracking simülasyonu tamamlandı.")

if __name__ == "__main__":
    main()