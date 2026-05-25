import cv2
import json
import os
import numpy as np

JSON_YOLU = "data/farm_zones.json"
TEST_FOTO_YOLU = r"dataset\CFR-0322-TR-15\combined_frame_27_jpg.rf.v4FcWXZ8IUmh8B0YoDZ5.jpg"

noktalar = []
ekran_olcegi = 1.0

def tiklama_olayi(olay, x, y, flags, param):
    global noktalar, ekran_olcegi
    if olay == cv2.EVENT_LBUTTONDOWN:
        gercek_x = int(x / ekran_olcegi)
        gercek_y = int(y / ekran_olcegi)
        noktalar.append([gercek_x, gercek_y])
        print(f"📍 Nokta eklendi: ({gercek_x}, {gercek_y})")

def json_kaydet(kamera_adi, bolge_adi, koordinatlar):
    if os.path.exists(JSON_YOLU):
        with open(JSON_YOLU, "r", encoding="utf-8") as f:
            try:
                veri = json.load(f)
            except json.JSONDecodeError:
                veri = {}
    else:
        veri = {}

    if kamera_adi not in veri:
        veri[kamera_adi] = {}

    veri[kamera_adi][bolge_adi] = koordinatlar

    with open(JSON_YOLU, "w", encoding="utf-8") as f:
        json.dump(veri, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ BAŞARILI: '{bolge_adi}' bölgesi kaydedildi!")

def main():
    global noktalar, ekran_olcegi
    print("--- 🗺️ AKILLI ÇİFTLİK BÖLGE SEÇİCİ (Hayalet Çizim Özellikli) ---")
    kamera_adi = input("Kamera veya Açı adını girin (Örn: kamera_1): ")
    bolge_adi = input("Çizeceğiniz bölgenin adını girin (Örn: dinlenme_alani): ")

    img = cv2.imread(TEST_FOTO_YOLU)
    if img is None:
        print(f"\n❌ Hata: Fotoğraf bulunamadı!")
        return

    MAX_EKRAN_GENISLIK = 1280
    orj_h, orj_w = img.shape[:2]

    if orj_w > MAX_EKRAN_GENISLIK:
        ekran_olcegi = MAX_EKRAN_GENISLIK / orj_w
        yeni_w = int(orj_w * ekran_olcegi)
        yeni_h = int(orj_h * ekran_olcegi)
        gosterim_resmi = cv2.resize(img, (yeni_w, yeni_h))
    else:
        ekran_olcegi = 1.0
        gosterim_resmi = img.copy()

    # --- ÖNCEKİ ÇİZİMLERİ JSON'DAN YÜKLE ---
    mevcut_bolgeler = {}
    if os.path.exists(JSON_YOLU):
        with open(JSON_YOLU, "r", encoding="utf-8") as f:
            try:
                veri = json.load(f)
                if kamera_adi in veri:
                    mevcut_bolgeler = veri[kamera_adi]
            except:
                pass

    pencere_ismi = f"Bolge Secici - [{kamera_adi} > {bolge_adi}] | Kaydet: 'S' | Temizle: 'C' | Cikis: 'Q'"
    cv2.namedWindow(pencere_ismi, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(pencere_ismi, tiklama_olayi)

    print("\nFotoğraf açıldı. Köşelere tıklayarak alanı belirleyin.")
    
    while True:
        kopya_img = gosterim_resmi.copy()
        
        # 1. Eski çizimleri ekrana yansıt (Hayalet Çizgiler)
        for m_bolge, m_koordinatlar in mevcut_bolgeler.items():
            # Eğer şu an o bölgeyi baştan çiziyorsak, eskisini ekranda gösterme (kafa karıştırmasın)
            if m_bolge == bolge_adi:
                continue 
                
            # Koordinatları ekrana sığacak şekilde ölçekle
            pts = np.array([[int(x * ekran_olcegi), int(y * ekran_olcegi)] for x, y in m_koordinatlar], np.int32)
            
            # Turuncu renkli çizgiler ve isim etiketleri ekle
            cv2.polylines(kopya_img, [pts], True, (0, 165, 255), 2) 
            cv2.putText(kopya_img, m_bolge, (pts[0][0], pts[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        
        # 2. Şu an senin çizdiğin aktif noktaları göster
        for i, nokta in enumerate(noktalar):
            ekran_x = int(nokta[0] * ekran_olcegi)
            ekran_y = int(nokta[1] * ekran_olcegi)
            ekran_noktasi = (ekran_x, ekran_y)

            cv2.circle(kopya_img, ekran_noktasi, 5, (0, 0, 255), -1) 
            if i > 0:
                prev_ekran_x = int(noktalar[i-1][0] * ekran_olcegi)
                prev_ekran_y = int(noktalar[i-1][1] * ekran_olcegi)
                cv2.line(kopya_img, (prev_ekran_x, prev_ekran_y), ekran_noktasi, (0, 255, 0), 2)
        
        if len(noktalar) > 2:
            ilknokta_ekran = (int(noktalar[0][0] * ekran_olcegi), int(noktalar[0][1] * ekran_olcegi))
            sonnokta_ekran = (int(noktalar[-1][0] * ekran_olcegi), int(noktalar[-1][1] * ekran_olcegi))
            cv2.line(kopya_img, sonnokta_ekran, ilknokta_ekran, (0, 255, 0), 2)

        cv2.imshow(pencere_ismi, kopya_img)
        tus = cv2.waitKey(1) & 0xFF

        if tus == ord('s'):
            if len(noktalar) >= 3:
                json_kaydet(kamera_adi, bolge_adi, noktalar)
                break
            else:
                print("\n⚠️ Uyarı: En az 3 nokta seçmelisiniz!")
        elif tus == ord('c'):
            noktalar = []
            print("\n🧹 Noktalar temizlendi.")
        elif tus == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()