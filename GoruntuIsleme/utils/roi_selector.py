import cv2
import json
import os

# Tıklanan koordinatları tutacağımız geçici liste
noktalar = []

def fare_olayi(event, x, y, flags, param):
    global noktalar
    # Sol tıklandığında x,y koordinatlarını kaydet
    if event == cv2.EVENT_LBUTTONDOWN:
        noktalar.append((x, y))
        print(f"Nokta eklendi: ({x}, {y})")

def bolge_secici():
    global noktalar
    
    # DİKKAT: Buraya dataset içindeki herhangi bir resmin TAM ADINI yazmalısın
    resim_yolu = "dataset/CFR-0322-TR-15/006_mp4-0000_jpg.rf.r6CqSp9KZCnazWFLFtUO.jpg" 
    
    if not os.path.exists(resim_yolu):
        print(f"Hata: {resim_yolu} bulunamadı. Lütfen koddaki resim adını düzeltin.")
        return

    resim = cv2.imread(resim_yolu)
    
    # Terminalden çizilecek alanın adını iste
    bolge_adi = input("Çizeceğiniz bölgenin adını girin (Örn: suluk, yemlik, dinlenme_alani): ")
    print(f"\nLütfen görüntü üzerinde '{bolge_adi}' alanının köşelerine sol tıklayarak çizin.")
    print("Çizimi bitirip kaydetmek için 'q' tuşuna basın.")

    cv2.namedWindow("Alan Belirleme Araci", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Alan Belirleme Araci", 1280, 720)
    cv2.setMouseCallback("Alan Belirleme Araci", fare_olayi)

    while True:
        resim_gosterim = resim.copy()
        
        # Tıklanan noktaları ekranda çizgiyle birleştir
        if len(noktalar) > 0:
            for i in range(len(noktalar)):
                cv2.circle(resim_gosterim, noktalar[i], 5, (0, 0, 255), -1)
                if i > 0:
                    cv2.line(resim_gosterim, noktalar[i-1], noktalar[i], (0, 255, 0), 2)
            # Son nokta ile ilk noktayı birleştirip kapalı bir şekil oluştur
            if len(noktalar) > 2:
                cv2.line(resim_gosterim, noktalar[-1], noktalar[0], (0, 255, 0), 2)

        cv2.imshow("Alan Belirleme Araci", resim_gosterim)
        
        # Klavyeden 'q' tuşuna basılırsa çık
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

    # Çizilen koordinatları JSON olarak data/ klasörüne kaydet
    if len(noktalar) > 2:
        kayit_yolu = "data/farm_zones.json"
        veri = {}
        
        # Eğer daha önceden çizilmiş alanlar varsa onları da oku, üstüne yazma
        if os.path.exists(kayit_yolu):
            with open(kayit_yolu, "r", encoding="utf-8") as f:
                veri = json.load(f)
        
        veri[bolge_adi] = noktalar
        
        with open(kayit_yolu, "w", encoding="utf-8") as f:
            json.dump(veri, f, indent=4, ensure_ascii=False)
            
        print(f"\nBaşarılı! '{bolge_adi}' alanı kaydedildi. Koordinatlar: {noktalar}")
    else:
        print("\nUyarı: Geçerli bir alan (en az 3 nokta) çizmediniz, kayıt yapılmadı.")

if __name__ == "__main__":
    bolge_secici()