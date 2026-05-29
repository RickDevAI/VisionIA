import os
import csv
from ultralytics import YOLO

# =========================
# CONFIGURAÇÕES
# =========================
BASE_MODEL   = "yolov8n-cls.pt"  
DATASET_DIR  = "dataset"
PROJECT_NAME = "visionia_cls"
EPOCHS       = 60                  
IMG_SIZE     = 224                
BATCH        = 16
DEVICE       = "0" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"


def treinar():
    model = YOLO(BASE_MODEL)

    results = model.train(
        data       = DATASET_DIR,
        epochs     = EPOCHS,
        imgsz      = IMG_SIZE,
        batch      = BATCH,
        name       = PROJECT_NAME,
        device     = DEVICE,
        cos_lr     = True,          
        dropout    = 0.3,           
        patience   = 15,            
        augment    = True,
        fliplr     = 0.5,
        degrees    = 10.0,          
        translate  = 0.1,
        scale      = 0.2,
        hsv_h      = 0.02,
        hsv_s      = 0.5,
        hsv_v      = 0.3,
        erasing    = 0.3,
        auto_augment = "randaugment",
        verbose    = True,
        plots      = True,
    )

    print("\n" + "="*50)
    print("TREINAMENTO CONCLUÍDO")
    print(f"Melhor accuracy_top1 : {results.results_dict.get('metrics/accuracy_top1', 'N/A')}")
    print(f"Pesos salvos em      : runs/classify/{PROJECT_NAME}/weights/best.pt")
    print("="*50)

    return results


if __name__ == "__main__":
    treinar()
