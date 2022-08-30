from djitellopy import tello
import KeyPressModule as kp
import time
import cv2
import numpy as np

kp.init()
me = tello.Tello()
me.connect()
print(me.get_battery())
global img
me.streamon()

def getKeyboardInput():

    lr, fb, ud, yv = 0, 0, 0, 0

    speed = 50
    if kp.getKey("LEFT"): lr = -speed
    elif kp.getKey("RIGHT"): lr = speed

    if kp.getKey("UP"): fb = speed
    elif kp.getKey("DOWN"): fb = -speed

    if kp.getKey("w"):ud = speed
    elif kp.getKey("s"): ud = -speed

    if kp.getKey("a"):yv = -speed
    elif kp.getKey("d"): yv = speed

    if kp.getKey("q"): me.land(); time.sleep(3)
    if kp.getKey("e"):  me.takeoff()

    if kp.getKey('z'):
        cv2.imwrite(f'Resources/Images/{time.time()}.jpg',img)
        time.sleep(0.3)

    return [lr, fb, ud, yv]

while True:

    vals = getKeyboardInput()

    me.send_rc_control(vals[0], vals[1], vals[2], vals[3])

    frame = me.get_frame_read().frame

    #img = cv2.resize(img, (360, 240))

    frame = cv2.resize(frame, (360, 240))
    hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    bound_lower = np.array([120-10, 30, 30])
    bound_upper = np.array([120+10, 255, 255])

    mask_green = cv2.inRange(hsv_img, bound_lower, bound_upper)
    kernel = np.ones((7, 7), np.uint8)

    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_CLOSE, kernel)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)

    seg_img = cv2.bitwise_and(frame, frame, mask=mask_green)
    contours, hier = cv2.findContours(mask_green.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    output = cv2.drawContours(seg_img, contours, -1, (0, 0, 255), 3)

    cv2.imshow("Result", output)

    cv2.waitKey(1)