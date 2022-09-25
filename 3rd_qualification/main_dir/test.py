import torch
import cv2
import numpy as np

#          x1 (pixels)  y1 (pixels)  x2 (pixels)  y2 (pixels)   confidence        class
# tensor([[4.13370e+02, 2.51479e+02, 6.40000e+02, 4.80000e+02, 2.58489e-01, 0.00000e+00]])

model = torch.hub.load('ultralytics/yolov5', 'custom', path='C:\\Users\\user\\PycharmProjects\\LockheedMatin\\3rd_qualification\\main_dir\\last.pt', force_reload=True)
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()

    results = model(frame, size=640)

    result = cv2.imshow('YOLO', np.squeeze(results.render()))
    xyxy = []

    for i in range(4):
        xyxy.append(int(results.xyxy[i]))

    print(xyxy)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()