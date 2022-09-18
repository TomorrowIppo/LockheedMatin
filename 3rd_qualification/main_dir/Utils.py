import cv2
import numpy as np
import math
from enum import Enum, auto

# --------------------------------------------------------------------

width = 640  # WIDTH OF THE IMAGE
height = 480  # HEIGHT OF THE IMAGE
deadZone = 60

# --------------------------------------------------------------------


frameWidth = width
frameHeight = height
global center_block_area
center_block_area = int((frameWidth / 3) * (frameHeight / 3))


# 명령용 enum 클래스
class Order(Enum):
    default_mode = auto()

    GO_LEFT = auto()
    TURN_LEFT = auto()

    GO_RIGHT = auto()
    TURN_RIGHT = auto()

    DO_SEARCH = auto()

    GO_UP = auto()
    GO_DOWN = auto()

    GO_FORWARD = auto()
    GO_BACKWARD = auto()

    GO_POS1 = auto()
    GO_POS2 = auto()
    GO_POS3 = auto()
    GO_POS4 = auto()


def process(img_input):
    gray = cv2.cvtColor(img_input, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(gray, (28, 28), interpolation=cv2.INTER_AREA)

    (thresh, img_binary) = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    h,w = img_binary.shape

    ratio = 100 / h
    new_h = 100
    new_w = w * ratio

    img_empty = np.zeros((110, 110), dtype=img_binary.dtype)
    img_binary = cv2.resize(img_binary, (int(new_w), int(new_h)), interpolation=cv2.INTER_AREA)
    img_empty[:img_binary.shape[0], :img_binary.shape[1]] = img_binary

    img_binary = img_empty

    cnts = cv2.findContours(img_binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


    # 컨투어의 무게중심 좌표를 구합니다.
    M = cv2.moments(cnts[0][0])
    center_x = (M["m10"] / M['m00'])
    center_y = (M['m01'] / M['m00'])

    # 무게 중심이 이미지 중심으로 오도록 이동시킵니다.
    height, width = img_binary.shape[:2]
    shiftx = width/2 - center_x
    shifty = height/2 - center_y

    Translation_Matrix = np.float32([[1, 0, shiftx], [0, 1, shifty]])
    img_binary = cv2.warpAffine(img_binary, Translation_Matrix, (width, height))


    img_binary = cv2.resize(img_binary, (28, 28), interpolation=cv2.INTER_AREA)
    flatten = img_binary.flatten() / 255.0

    return flatten


def stackImages(scale, imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range(0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape[:2]:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]),
                                                None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y] = cv2.cvtColor(imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank] * rows
        hor_con = [imageBlank] * rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None, scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor = np.hstack(imgArray)
        ver = hor
    return ver


def getContours(img, imgContour, color, detect_color, init_QR_height, log_str, searching_mode, dir):
    global center_block_area
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if len(contours) != 0 and searching_mode:
        __cnt = contours[0]
        __area = cv2.contourArea(__cnt)

        for cnt in contours:
            area = cv2.contourArea(cnt)

            if __area <= area:
                __area = area

            # areaMin = cv2.getTrackbarPos("Area", "Parameters")
            if __area > 250:
                cv2.drawContours(imgContour, cnt, -1, (255, 0, 255), 7)
                peri = cv2.arcLength(__cnt, True)
                approx = cv2.approxPolyDP(__cnt, 0.02 * peri, True)
                # print(len(approx))
                x, y, w, h = cv2.boundingRect(approx)
                cx = int(x + (w / 2))  # CENTER X OF THE OBJECT
                cy = int(y + (h / 2))  # CENTER Y OF THE OBJECT

                if cx > (int(frameWidth / 2) + deadZone) and cy < (int(frameHeight / 2) - deadZone):
                    cv2.putText(imgContour, ' GO POS1 ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    dir = Order.GO_POS1
                elif cx < (int(frameWidth / 2) - deadZone) and cy < (int(frameHeight / 2) - deadZone):
                    cv2.putText(imgContour, ' GO POS2 ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    dir = Order.GO_POS2
                elif cx < (int(frameWidth / 2) - deadZone) and cy > (int(frameHeight / 2) + deadZone):
                    cv2.putText(imgContour, ' GO POS3 ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    dir = Order.GO_POS3
                elif cx > (int(frameWidth / 2) + deadZone) and cy > (int(frameHeight / 2) + deadZone):
                    cv2.putText(imgContour, ' GO POS4 ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    dir = Order.GO_POS4
                elif cx < (int(frameWidth / 2) - deadZone):
                    cv2.putText(imgContour, ' TURN LEFT ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    # cv2.rectangle(imgContour, (0, int(frameHeight/2-deadZone)), (int(frameWidth/2)-deadZone, int(frameHeight/2)+deadZone), (0, 0, 255), cv2.FILLED)
                    dir = Order.TURN_LEFT
                elif cx > (int(frameWidth / 2) + deadZone):
                    cv2.putText(imgContour, ' TURN RIGHT ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    # cv2.rectangle(imgContour, (int(frameWidth/2+deadZone), int(frameHeight/2-deadZone)), (frameWidth, int(frameHeight/2)+deadZone), (0, 0, 255), cv2.FILLED)
                    dir = Order.TURN_RIGHT
                elif cy < (int(frameHeight / 2) - deadZone):
                    cv2.putText(imgContour, ' GO UP ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    # cv2.rectangle(imgContour, (int(frameWidth/2-deadZone), 0), (int(frameWidth/2+deadZone), int(frameHeight/2)-deadZone), (0, 0, 255), cv2.FILLED)
                    dir = Order.GO_UP
                elif cy > (int(frameHeight / 2) + deadZone):
                    cv2.putText(imgContour, ' GO DOWN ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    # cv2.rectangle(imgContour, (int(frameWidth/2-deadZone), int(frameHeight/2)+deadZone), (int(frameWidth/2+deadZone), frameHeight), (0, 0, 255), cv2.FILLED)
                    dir = Order.GO_DOWN
                else:
                    if ((center_block_area - 8000) <= int(__area)) and (int(__area) <= (center_block_area + 4000)):
                        # dir = Order.default_mode
                        # QR 위치로 고도 조정
                        init_QR_height = True
                        searching_mode = False

                        print(f'{color} 중심 영역 도달')
                        log_str += f'{color} 중심 영역 도달\n'
                        print(f'Area : {__area}')
                        log_str += f'Area : {__area}\n'
                        detect_color = True
                        print(f'detect Color : {color}')
                        log_str += f'detect Color : {color}\n'

                        print(f'center_block_area = {center_block_area}')
                        log_str += f'center_block_area = {center_block_area}\n'
                        dir = Order.default_mode


                    elif int(__area) > center_block_area + 4000:
                        dir = Order.GO_BACKWARD
                        print(f'기준치보다 큼, area = {__area}')
                        log_str += f'기준치보다 큼, area = {__area}\n'
                    elif int(__area) < center_block_area - 8000:
                        dir = Order.GO_FORWARD
                        print(f'기준치보다 작음, area = {__area}')
                        log_str += f'기준치보다 작음, area = {__area}\n'
                    else:
                        pass

                cv2.line(imgContour, (int(frameWidth / 2), int(frameHeight / 2)), (cx, cy), (0, 0, 255), 3)
                cv2.rectangle(imgContour, (x, y), (x + w, y + h), (0, 255, 0), 5)
                cv2.putText(imgContour, "Points: " + str(len(approx)), (x + w + 20, y + 20), cv2.FONT_HERSHEY_COMPLEX,
                            .7, (0, 255, 0), 2)
                cv2.putText(imgContour, "Area: " + str(int(__area)), (x + w + 20, y + 45), cv2.FONT_HERSHEY_COMPLEX,
                            0.7, (0, 255, 0), 2)
                cv2.putText(imgContour, " " + str(int(x)) + " " + str(int(y)), (x - 20, y - 45),
                            cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 0), 2)
            else:
                dir = Order.default_mode
    elif searching_mode:
        dir = Order.DO_SEARCH
    elif not searching_mode:
        pass
    else:
        dir = Order.default_mode
        log_str += 'getContours에서 디폴트\n'


def display(img):
    cv2.line(img, (int(frameWidth / 2) - deadZone, 0), (int(frameWidth / 2) - deadZone, frameHeight), (255, 255, 0), 3)
    cv2.line(img, (int(frameWidth / 2) + deadZone, 0), (int(frameWidth / 2) + deadZone, frameHeight), (255, 255, 0), 3)
    cv2.circle(img, (int(frameWidth / 2), int(frameHeight / 2)), 5, (0, 0, 255), 5)
    cv2.line(img, (0, int(frameHeight / 2) - deadZone), (frameWidth, int(frameHeight / 2) - deadZone), (255, 255, 0), 3)
    cv2.line(img, (0, int(frameHeight / 2) + deadZone), (frameWidth, int(frameHeight / 2) + deadZone), (255, 255, 0), 3)


def QR(img, log_str, start_hover, QR_hover_detect, is_save_drone_height, qr_data):
    qrDecoder = cv2.QRCodeDetector()

    data, bbox, rectifiedImage = qrDecoder.detectAndDecode(img)
    if len(data) > 0:
        if data == 'hover':
            print("Decoded Data : {}".format(data))
            log_str += f'Decoded Data : {data}\n'
            start_hover = True
            QR_hover_detect = True
        else:
            result = qr_calc(data)
            print("Decoded Data : {}".format(data))
            log_str += f'Decoded Data : {data}\n'
            print(f'result : {result}')
            log_str += f'result : {result}\n'
            is_save_drone_height = True
            qr_data = result
            return result

    return None


def qr_calc(_str):
    list_str = list(_str)
    first_num = 0
    second_num = 0
    result = 0

    if _str.find('+') != -1:
        # print('+')
        idx = _str.find('+')
        for i in range(idx):
            first_num += int(list_str[i]) * math.pow(10, idx - 1 - i)
        for i in range(idx + 1, len(list_str)):
            second_num += int(list_str[i]) * math.pow(10, len(list_str) - 1 - i)
        result = int(first_num + second_num)

    elif _str.find('-') != -1:
        # print('-')
        idx = _str.find('-')
        for i in range(idx):
            first_num += int(list_str[i]) * math.pow(10, idx - 1 - i)
        for i in range(idx + 1, len(list_str)):
            second_num += int(list_str[i]) * math.pow(10, len(list_str) - 1 - i)
        result = int(first_num - second_num)

    elif _str.find('*') != -1:
        # print('*')
        idx = _str.find('*')
        for i in range(idx):
            first_num += int(list_str[i]) * math.pow(10, idx - 1 - i)
        for i in range(idx + 1, len(list_str)):
            second_num += int(list_str[i]) * math.pow(10, len(list_str) - 1 - i)
        result = int(first_num * second_num)

    elif _str.find('/') != -1:
        # print('/')
        idx = _str.find('/')
        for i in range(idx):
            first_num += int(list_str[i]) * math.pow(10, idx - 1 - i)
        for i in range(idx + 1, len(list_str)):
            second_num += int(list_str[i]) * math.pow(10, len(list_str) - 1 - i)
        result = int(first_num / second_num)

    return result


def do_action(drone, num):
    global log_str
    global dir
    global init_height

    if num == 1:
        print(f'num = {num}')
        log_str += f'num = {num}\n'
        drone.move_up(30)
        drone.move_down(30)
        init_height = True

    elif num == 2:
        print(f'num = {num}')
        log_str += f'num = {num}\n'
        # 안전거리 확보
        drone.move_back(20)
        drone.flip_forward()
        init_height = True

    elif num == 3:
        print(f'num = {num}')
        log_str += f'num = {num}\n'
        drone.move_down(30)
        drone.move_up(30)
        init_height = True

    elif num == 4:
        print(f'num = {num}')
        log_str += f'num = {num}\n'
        # 안전거리 확보
        drone.move_right(20)
        drone.flip_left()
        init_height = True

    elif num == 5:
        print(f'num = {num}')
        log_str += f'num = {num}\n'
        drone.rotate_clockwise(360)
        init_height = True
    else:
        pass


def handwritten_do_daction(drone, digit):
    global log_str
    global dir
    global init_height

    if digit == 1:
        print(f'digit = {digit}')
        log_str += f'digit = {digit}\n'
        drone.move_back(30)
        drone.move_forward(30)
        init_height = True

    elif digit == 2:
        print(f'digit = {digit}')
        log_str += f'digit = {digit}\n'
        # 안전거리 확보
        drone.move_left(30)
        drone.move_right(30)
        init_height = True

    elif digit == 3:
        print(f'digit = {digit}')
        log_str += f'digit = {digit}\n'
        drone.rotate_clockwise(360)
        init_height = True

    elif digit == 4:
        print(f'digit = {digit}')
        log_str += f'digit = {digit}\n'
        # 안전거리 확보
        drone.move_right(10)
        drone.move_up(10)
        drone.move_left(10)
        drone.move_down(10)
        init_height = True

    elif digit == 5:
        print(f'num = {digit}')
        log_str += f'num = {digit}\n'
        drone.flip_backward()
        init_height = True

    elif digit == 6:
        print(f'num = {digit}')
        log_str += f'num = {digit}\n'
        drone.move_up(30)
        drone.flip_backward()
        drone.move_down(30)
        init_height = True

    elif digit == 7:
        print(f'num = {digit}')
        log_str += f'num = {digit}\n'
        drone.flip_left()
        init_height = True

    elif digit == 8:
        print(f'num = {digit}')
        log_str += f'num = {digit}\n'
        drone.move_up(30)
        drone.move_down(30)
        init_height = True

    elif digit == 9:
        print(f'num = {digit}')
        log_str += f'num = {digit}\n'
        drone.flip_backward()
        init_height = True

    else:
        pass
