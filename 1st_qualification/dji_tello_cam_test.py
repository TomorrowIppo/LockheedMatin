from djitellopy import tello
from time import sleep
import cv2
import numpy as np

me = tello.Tello()
me.connect()
print(me.get_battery())
me.streamoff()
me.streamon()
#me.takeoff()

global red_detect
red_detect = False
global green_detect
green_detect = False
global blue_detect
blue_detect = False
global qr_detect
qr_detect = False


def calc_func(qr_str):
    my_str = list(qr_str)

    if my_str[1] == '+':
        return int(my_str[0]) + int(my_str[2])
    elif my_str[1] == '-':
        return int(my_str[0]) - int(my_str[2])
    elif my_str[1] == '*':
        return int(my_str[0]) * int(my_str[2])
    elif my_str[1] == 'x':
        return int(my_str[0]) * int(my_str[2])
    elif my_str[1] == '/':
        return int(my_str[0]) / int(my_str[2])


def cv():
    global red_detect, green_detect, blue_detect, qr_detect
    frame = me.get_frame_read().frame

    #frame = cv2.resize(frame, (360, 240))
    # qr 시작
    frame = cv2.resize(frame, None, fx=0.2, fy=0.2, interpolation=cv2.INTER_AREA)

    qrDecoder = cv2.QRCodeDetector()

    # QR코드를 찾고 디코드해줍니다
    data, bbox, rectifiedImage = qrDecoder.detectAndDecode(frame)
    if len(data) > 0:
        if not qr_detect:
            qr_detect = True
        print("Decoded Data : {}".format(data))
        print(f'result : {calc_func(data)}')
        #rectifiedImage = np.uint8(rectifiedImage)
    # qr 끝

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([110, 100, 100])  # 파랑색 범위
    upper_blue = np.array([130, 255, 255])

    lower_green = np.array([50, 150, 50])  # 초록색 범위
    upper_green = np.array([80, 255, 255])

    lower_red = np.array([0, 100, 100])
    upper_red = np.array([7, 255, 255])

    # Threshold the HSV image to get only blue colors
    mask = cv2.inRange(hsv, lower_red, upper_red)  # 110<->150 Hue(색상) 영역을 지정.
    mask1 = cv2.inRange(hsv, lower_green, upper_green)  # 영역 이하는 모두 날림 검정. 그 이상은 모두 흰색 두개로 Mask를 씌움.
    mask2 = cv2.inRange(hsv, lower_blue, upper_blue)

    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(frame, frame, mask=mask)  # 흰색 영역에 파랑색 마스크를 씌워줌.
    res1 = cv2.bitwise_and(frame, frame, mask=mask1)  # 흰색 영역에 초록색 마스크를 씌워줌.
    res2 = cv2.bitwise_and(frame, frame, mask=mask2)  # 흰색 영역에 빨강색 마스크를 씌워줌.


    # Red
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) != 0:
        for contour in contours:
            if cv2.contourArea(contour) > 500:
                #print("red detected")
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                if red_detect is False:
                    red_detect = True
                    #me.move_down(10)
                print('RED')
                    # print("red detected")
                #red_detect_img = cv2.imwrite('red_detect_img.png', frame)


    # Green
    contours1, hierarchy1 = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours1) != 0:
        for contour in contours1:
            if cv2.contourArea(contour) > 500:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                #print("green detected")
                if green_detect is False:
                    green_detect = True
                print("GREEN")
                #green_detect_img = cv2.imwrite('green_detect_img.png', frame)



    # Blue
    contours2, hierarchy2 = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours2) != 0:
        for contour in contours2:
            if cv2.contourArea(contour) > 500:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                if blue_detect is False:
                    blue_detect = True
                print("BLUE")
                #blue_detect_img = cv2.imwrite('blue_detect_img.png', frame)



    cv2.imshow('frame', frame)  # 원본 영상을 보여줌
    # cv2.imshow('Blue', res)  # 마스크 위에 파랑색을 씌운 것을 보여줌.
    # cv2.imshow('Green', res1)  # 마스크 위에 초록색을 씌운 것을 보여줌.
    # cv2.imshow('red', res2)  # 마스크 위에 빨강색을 씌운 것을 보여줌.


while True:
    cv()
    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break