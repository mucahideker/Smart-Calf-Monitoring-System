from ultralytics import YOLO

# 1. Eğitilmemiş temiz (Nano) modeli alıyoruz
model = YOLO("yolo11n.pt") 

print("Eğitim başlıyor... Bu işlem bilgisayarının hızına göre biraz sürebilir.")

# 2. Modeli kendi veri setimizle (data.yaml) eğitiyoruz
# epochs=50 demek, model 231 fotoğrafı tam 50 kere baştan sona çalışacak demek.
model.train(
    data="buzagi_veriseti/data.yaml", 
    epochs=50, 
    imgsz=640, 
    batch=8,
    name="buzagi_modelimiz"
)

print("Eğitim tamamlandı! Model ağırlıkları 'runs/detect/buzagi_modelimiz/weights/best.pt' konumuna kaydedildi.")