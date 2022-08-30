import cv2
import numpy as np

cap = cv2.VideoCapture(0)
while(1):
    ret, frame = cap.read()
    frame = cv2.resize(frame, (360, 240))
    hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    bound_lower = np.array([25, 20, 20])
    bound_upper = np.array([100, 255, 255])

    mask_green = cv2.inRange(hsv_img, bound_lower, bound_upper)
    kernel = np.ones((7,7),np.uint8)

    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_CLOSE, kernel)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)

    seg_img = cv2.bitwise_and(frame, frame, mask=mask_green)
    contours, hier = cv2.findContours(mask_green.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    output = cv2.drawContours(seg_img, contours, -1, (0, 0, 255), 3)

    cv2.imshow("Result", output)
    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cv2.destroyAllWindows()