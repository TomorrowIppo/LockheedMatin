import cv2
import numpy as np

cap = cv2.VideoCapture(0)
while(1):
    ret, inputImage = cap.read()
    inputImage = cv2.resize(inputImage, None, fx=0.2, fy=0.2, interpolation=cv2.INTER_AREA)

    qrDecoder = cv2.QRCodeDetector()

    # QR코드를 찾고 디코드해줍니다
    data, bbox, rectifiedImage = qrDecoder.detectAndDecode(inputImage)
    if len(data) > 0:
        print("Decoded Data : {}".format(data))
        rectifiedImage = np.uint8(rectifiedImage)
