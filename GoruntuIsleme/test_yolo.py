from ultralytics import YOLO

model = YOLO("runs/detect/buzagi_modelimiz/weights/best.pt")

# BURAYA TR-15'TEKİ FOTOĞRAFIN YOLUNU GİRİYORUZ JPG YADA PNG OLMASINA DİKKAT ET
foto_yolu = r"dataset\CFR-0322-TR-15\vlc-record-2025-03-26-08h42m56s-rtsp___sav_itechrobotics_com_tr_7554_-_mp4-0061_jpg.rf.O0SwJggVpTBBTdzAiV6j.jpg"

model.predict(source=foto_yolu, show=True)
model.predict(source=foto_yolu, save=True)