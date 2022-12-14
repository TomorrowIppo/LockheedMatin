from djitellopy import Tello
import tensorflow as tf
from enum import Enum, auto
import numpy as np
import math
import cv2
import torch
import time

#          x1 (pixels)  y1 (pixels)  x2 (pixels)  y2 (pixels)   confidence        class
# tensor([[4.13370e+02, 2.51479e+02, 6.40000e+02, 4.80000e+02, 2.58489e-01, 0.00000e+00]])

model = torch.hub.load('ultralytics/yolov5', 'custom', path='C:\\Users\\user\\PycharmProjects\\LockheedMatin\\3rd_qualification\\main_dir\\last.pt', force_reload=True)


# --------------------------------------------------------------------

width = 640  # WIDTH OF THE IMAGE
height = 480  # HEIGHT OF THE IMAGE
deadZone = 60
threshold = 0.90

# --------------------------------------------------------------------


# --------------------------------------------------------------------

start_time = time.time()
hover_time = 0
init_hover_time = True
global init_digit_height
init_digit_height = False
global digit_height_1
digit_height_1 = False
global digit_height_2
digit_height_2 = False

default_drone_up_down = 10
slow_drone_up_down = 5
default_drone_right_left = 10
slow_drone_right_left = 5
default_drone_forward_backward = 10
slow_drone_forward_backward = 5
default_drone_yaw = 30
slow_drone_yaw = 5

QR_hover_detect = False
start_hover = False
global init_height
init_height = True

global detect_G
detect_G = False
digit_G = False

global detect_R
detect_R = False
digit_R = False

global detect_B
detect_B = False
digit_B = False

global searching_mode
searching_mode = False

global is_save_drone_height
is_save_drone_height = False
save_drone_height = None
global qr_data
qr_data = None

global is_done_mission
is_done_mission = True

lower_blue = np.array([100, 150, 0])
upper_blue = np.array([140, 255, 255])

lower_green = np.array([0, 0, 0])
upper_green = np.array([360, 255, 50])

lower_red = np.array([0, 50, 50])
upper_red = np.array([10, 255, 255])

f = open("dji_tello_main_test_log.txt", 'w')
global log_str
log_str = ''


frameWidth = width
frameHeight = height
global center_block_area
center_block_area = int((frameWidth / 3) * (frameHeight / 3))
# cap = cv2.VideoCapture(1)
# cap.set(3, frameWidth)
# cap.set(4, frameHeight)
# cap.set(10,200)


global imgContour
global dir


# drone, web_cam ????????? ?????????, ??????
class Cam(Enum):
    DRONE = auto()
    WEBCAM = auto()


# ????????? enum ?????????
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


def getContours(img, imgContour, detect_color, xyxy, object_detect=False):
    global dir
    global searching_mode
    global detect_G
    global detect_R
    global detect_B
    global init_digit_height
    global log_str
    global center_block_area
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not object_detect:
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
                        dir = Order.TURN_LEFT

                    elif cx > (int(frameWidth / 2) + deadZone):
                        cv2.putText(imgContour, ' TURN RIGHT ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                        dir = Order.TURN_RIGHT

                    elif cy < (int(frameHeight / 2) - deadZone):
                        cv2.putText(imgContour, ' GO UP ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                        dir = Order.GO_UP

                    elif cy > (int(frameHeight / 2) + deadZone):
                        cv2.putText(imgContour, ' GO DOWN ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                        dir = Order.GO_DOWN

                    else:
                        if ((center_block_area - 8000) <= int(__area)) and (int(__area) <= (center_block_area + 4000)):
                            # dir = Order.default_mode
                            # QR ????????? ?????? ??????
                            init_digit_height = True
                            searching_mode = False

                            if detect_color == 'G':
                                print('G ?????? ?????? ??????')
                                log_str += 'G ?????? ?????? ??????\n'
                                print(f'Area : {__area}')
                                log_str += f'Area : {__area}\n'
                                detect_G = True
                                print('detect Color : Green')
                                log_str += 'detect Color : Green\n'

                            elif detect_color == 'R':
                                print('R ?????? ?????? ??????')
                                log_str += 'R ?????? ?????? ??????\n'
                                print(f'Area : {__area}')
                                log_str += f'Area : {__area}\n'
                                detect_R = True
                                print('detect Color : Red')
                                log_str += 'detect Color : Red\n'

                            elif detect_color == 'B':
                                print('B ?????? ?????? ??????')
                                log_str += 'B ?????? ?????? ??????\n'
                                print(f'Area : {__area}')
                                log_str += f'Area : {__area}\n'
                                detect_B = True
                                print('detect Color : Blue')
                                log_str += 'detect Color : Blue\n'

                            print(f'center_block_area = {center_block_area}')
                            log_str += f'center_block_area = {center_block_area}\n'
                            dir = Order.default_mode

                        elif int(__area) > center_block_area + 4000:
                            dir = Order.GO_BACKWARD
                            print(f'??????????????? ???, area = {__area}')
                            log_str += f'??????????????? ???, area = {__area}\n'

                        elif int(__area) < center_block_area - 8000:
                            dir = Order.GO_FORWARD
                            print(f'??????????????? ??????, area = {__area}')
                            log_str += f'??????????????? ??????, area = {__area}\n'

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
            log_str += 'getContours?????? ?????????\n'
    else:
        print('??????')
        if len(xyxy) != 0:
            cv2.rectangle(imgContour, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0, 255, 0), 5)


def display(img):
    cv2.line(img, (int(frameWidth / 2) - deadZone, 0), (int(frameWidth / 2) - deadZone, frameHeight), (255, 255, 0), 3)
    cv2.line(img, (int(frameWidth / 2) + deadZone, 0), (int(frameWidth / 2) + deadZone, frameHeight), (255, 255, 0), 3)
    cv2.circle(img, (int(frameWidth / 2), int(frameHeight / 2)), 5, (0, 0, 255), 5)
    cv2.line(img, (0, int(frameHeight / 2) - deadZone), (frameWidth, int(frameHeight / 2) - deadZone), (255, 255, 0), 3)
    cv2.line(img, (0, int(frameHeight / 2) + deadZone), (frameWidth, int(frameHeight / 2) + deadZone), (255, 255, 0), 3)


def handwritten_do_daction(_drone, digit):
    global log_str
    global dir
    global init_height

    if digit == 1:
        print(f'digit = {digit}')
        log_str += f'digit = {digit}\n'
        _drone.move_back(30)
        _drone.move_forward(30)
        init_height = True

    elif digit == 2:
        print(f'digit = {digit}')
        log_str += f'digit = {digit}\n'
        # ???????????? ??????
        _drone.move_left(30)
        _drone.move_right(30)
        init_height = True

    elif digit == 3:
        print(f'digit = {digit}')
        log_str += f'digit = {digit}\n'
        _drone.rotate_clockwise(360)
        init_height = True

    elif digit == 4:
        print(f'digit = {digit}')
        log_str += f'digit = {digit}\n'
        # ???????????? ??????
        _drone.move_right(10)
        _drone.move_up(10)
        _drone.move_left(10)
        _drone.move_down(10)
        init_height = True

    elif digit == 5:
        print(f'num = {digit}')
        log_str += f'num = {digit}\n'
        _drone.flip_backward()
        init_height = True

    elif digit == 6:
        print(f'num = {digit}')
        log_str += f'num = {digit}\n'
        _drone.move_up(30)
        _drone.flip_backward()
        _drone.move_down(30)
        init_height = True

    elif digit == 7:
        print(f'num = {digit}')
        log_str += f'num = {digit}\n'
        _drone.flip_left()
        init_height = True

    elif digit == 8:
        print(f'num = {digit}')
        log_str += f'num = {digit}\n'
        _drone.move_up(30)
        _drone.move_down(30)
        init_height = True

    elif digit == 9:
        print(f'num = {digit}')
        log_str += f'num = {digit}\n'
        _drone.flip_backward()
        init_height = True

    else:
        pass


def empty(a):
    pass

cv2.namedWindow("Parameters")
cv2.resizeWindow("Parameters", 640, 240)
cv2.createTrackbar("Threshold1", "Parameters", 166, 255, empty)
cv2.createTrackbar("Threshold2", "Parameters", 171, 255, empty)
cv2.createTrackbar("Area", "Parameters", 1750, 30000, empty)

color = None
detect_color = None
cap = None
drone = None
WIDTH = None
HEIGHT = None
my_cam = Cam.WEBCAM
if my_cam == Cam.WEBCAM:
    cap = cv2.VideoCapture(0)
    WIDTH = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    HEIGHT = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
elif my_cam == Cam.DRONE:
    # --------------------------------------------------------------------

    startCounter = True

    # CONNECT TO TELLO
    drone = Tello()
    drone.connect()
    drone.for_back_velocity = 0
    drone.left_right_velocity = 0
    drone.up_down_velocity = 0
    drone.yaw_velocity = 0
    drone.speed = 0

    print(drone.get_battery())
    log_str += ('drone_battery : ' + str(drone.get_battery()) + '%\n')

    drone.streamoff()
    drone.streamon()

    # --------------------------------------------------------------------

recog_w = 250
recog_h = 150
object_detection = True

try:
    while True:
        if my_cam == Cam.DRONE:
            # GET THE IMAGE FROM TELLO
            frame_read = drone.get_frame_read()
            myFrame = frame_read.frame

            img = cv2.resize(myFrame, (width, height))
            copy_img = img.copy()
            imgContour = img.copy()
            imgHsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            drone_height = drone.get_height()
            dir = Order.default_mode

            h_min = cv2.getTrackbarPos("HUE Min", "HSV")
            h_max = cv2.getTrackbarPos("HUE Max", "HSV")
            s_min = cv2.getTrackbarPos("SAT Min", "HSV")
            s_max = cv2.getTrackbarPos("SAT Max", "HSV")
            v_min = cv2.getTrackbarPos("VALUE Min", "HSV")
            v_max = cv2.getTrackbarPos("VALUE Max", "HSV")

            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])

            # takeoff
            if startCounter:
                drone.takeoff()
                startCounter = False

            # 0??????, ?????? ????????? ??????
            if init_height and not startCounter:
                print(f'------ ?????? ????????? ??? ({drone_height}) ------')
                log_str += f'------ ?????? ????????? ??? ({drone_height}) ------\n'
                if drone_height == 60:
                    init_height = False
                    print('------ ?????? ????????? ?????? ------')
                    log_str += '------ ?????? ????????? ?????? ------\n'
                    if QR_hover_detect:
                        drone.move_right(20)
                        searching_mode = True

                elif drone_height < 60:
                    dir = Order.GO_UP
                else:
                    dir = Order.GO_DOWN
            else:
                # 1??????, 'hover' QR ??????
                if not QR_hover_detect:
                    print('1?????? : hover QR ?????????')
                    log_str += '1?????? : hover QR ?????????\n'
                    qrDecoder = cv2.QRCodeDetector()

                    # hover QR??? ?????? ???
                    data, bbox, rectifiedImage = qrDecoder.detectAndDecode(img)
                    if len(data) > 0 and data == 'hover':
                        print("Decoded Data : {}".format(data))
                        log_str += f'Decoded Data : {data}\n'
                        rectifiedImage = np.uint8(rectifiedImage)
                        start_hover = True
                        QR_hover_detect = True

                # 1.5??????, 'hover' QR ?????? ??? ?????????
                if start_hover:
                    if init_hover_time:
                        print('????????? ??????')
                        log_str += '????????? ??????\n'
                        hover_time = time.time()
                        init_hover_time = False
                        dir = Order.default_mode
                    interval = time.time() - hover_time
                    if (5.0 <= interval) and (interval <= 5.1):
                        start_hover = False
                        print(f'????????? ???, interval : {interval}')
                        log_str += f'????????? ???, interval : {interval}\n'

                # 2??????, G R B ?????? ??? ?????? ?????? ??? ?????? ?????? ??????
                if QR_hover_detect and not start_hover:
                    searching_mode = True
                    print('2?????? : ?????? ', end='')
                    log_str += '2?????? : ?????? '
                    # Green ?????? ??????
                    if not detect_G:
                        print('Green ?????? ???')
                        log_str += 'Green ?????? ???\n'
                        lower = lower_green
                        upper = upper_green
                        detect_color = 'G'

                    # Green??? ???????????????, ????????? ??? ????????? ???
                    if detect_G and not digit_G:
                        searching_mode = False
                        digit = recognition_digit(img)
                        if init_digit_height:
                            print(f'------ ?????? ????????? ??? ({drone_height}) ------')
                            log_str += f'------ ?????? ????????? ??? ({drone_height}) ------\n'
                            if drone_height == 50:
                                init_digit_height = False
                                print('------ ?????? ????????? ?????? ------')
                                log_str += '------ ?????? ????????? ?????? ------\n'

                            elif drone_height < 50:
                                dir = Order.GO_UP
                            else:
                                dir = Order.GO_DOWN
                        # ????????? ?????? ?????? ?????? ????????? ?????????
                        if digit is not None:
                            digit_G = True
                            init_height = False
                            handwritten_do_daction(drone, digit)
                            searching_mode = False

                    # Green ?????? ??? Red ?????? ??????
                    if detect_G and not detect_R and digit_G:
                        print('Red ?????? ???')
                        log_str += 'Red ?????? ???\n'
                        lower = lower_red
                        upper = upper_red
                        detect_color = 'R'

                    # Red??? ???????????????, ????????? ??? ????????? ???
                    if detect_G and detect_R and not digit_R:
                        searching_mode = False
                        digit = recognition_digit(img)
                        if init_digit_height:
                            print(f'------ ?????? ????????? ??? ({drone_height}) ------')
                            log_str += f'------ ?????? ????????? ??? ({drone_height}) ------\n'
                            if drone_height == 50:
                                init_digit_height = False
                                print('------ ?????? ????????? ?????? ------')
                                log_str += '------ ?????? ????????? ?????? ------\n'

                            elif drone_height < 50:
                                dir = Order.GO_UP
                            else:
                                dir = Order.GO_DOWN
                        # ????????? ?????? ?????? ?????? ????????? ?????????
                        if digit is not None:
                            digit_R = True
                            init_height = False
                            handwritten_do_daction(drone, digit)
                            searching_mode = False

                    # Green, Red ?????? ??? Blue ?????? ??????
                    if detect_G and detect_R and not detect_B and digit_G and digit_R:
                        print('Blue ?????? ???')
                        log_str += 'Blue ?????? ???\n'
                        lower = lower_blue
                        upper = upper_blue
                        detect_color = 'B'

                    # Blue??? ???????????????, ????????? ??? ????????? ???
                    if detect_G and detect_R and detect_B and not digit_B:
                        searching_mode = False
                        digit = recognition_digit(img)
                        if init_digit_height:
                            print(f'------ ?????? ????????? ??? ({drone_height}) ------')
                            log_str += f'------ ?????? ????????? ??? ({drone_height}) ------\n'
                            if drone_height == 50:
                                init_digit_height = False
                                print('------ ?????? ????????? ?????? ------')
                                log_str += '------ ?????? ????????? ?????? ------\n'

                            elif drone_height < 50:
                                dir = Order.GO_UP
                            else:
                                dir = Order.GO_DOWN
                        # ????????? ?????? ?????? ?????? ????????? ?????????
                        if digit is not None:
                            digit_B = True
                            init_height = False
                            handwritten_do_daction(drone, digit)
                            searching_mode = False

                    # G, B, R??? QR??? ?????? ?????? ??? ?????? ??????
                    if digit_G and digit_R and digit_B:
                        raise KeyboardInterrupt

            mask = cv2.inRange(imgHsv, lower, upper)
            result = cv2.bitwise_and(img, img, mask=mask)
            mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

            # imgBlur = cv2.GaussianBlur(result, (7, 7), 1)
            imgBlur = cv2.medianBlur(result, 5)
            imgGray = cv2.cvtColor(imgBlur, cv2.COLOR_BGR2GRAY)
            threshold1 = cv2.getTrackbarPos("Threshold1", "Parameters")
            threshold2 = cv2.getTrackbarPos("Threshold2", "Parameters")
            imgCanny = cv2.Canny(imgGray, 50, 50)
            kernel = np.ones((5, 5))
            imgDil = cv2.dilate(imgCanny, kernel, iterations=1)

            getContours(imgDil, imgContour, color)
            display(imgContour)

            # GO_LEFT
            if dir == Order.GO_LEFT:
                drone.left_right_velocity = -10
                drone.for_back_velocity = 0
                drone.up_down_velocity = 0
                drone.yaw_velocity = 0

            # TURN_LEFT
            elif dir == Order.TURN_LEFT:
                drone.left_right_velocity = 0
                drone.for_back_velocity = 0
                drone.up_down_velocity = 0
                drone.yaw_velocity = -10

            # GO_RIGHT
            elif dir == Order.GO_RIGHT:
                drone.left_right_velocity = 10
                drone.for_back_velocity = 0
                drone.up_down_velocity = 0
                drone.yaw_velocity = 0

            # TURN_RIGHT
            elif dir == Order.TURN_RIGHT:
                drone.left_right_velocity = 0
                drone.for_back_velocity = 0
                drone.up_down_velocity = 0
                drone.yaw_velocity = 10

            # GO_UP
            elif dir == Order.GO_UP:
                drone.left_right_velocity = 0
                drone.for_back_velocity = 0
                drone.up_down_velocity = 15
                drone.yaw_velocity = 0

            # GO_DOWN
            elif dir == Order.GO_DOWN:
                drone.left_right_velocity = 0
                drone.for_back_velocity = 0
                drone.up_down_velocity = -15
                drone.yaw_velocity = 0

            # GO_FORWARD
            elif dir == Order.GO_FORWARD:
                drone.left_right_velocity = 0
                drone.for_back_velocity = 10
                drone.up_down_velocity = 0
                drone.yaw_velocity = 0

            # GO_BACKWARD
            elif dir == Order.GO_BACKWARD:
                drone.left_right_velocity = 0
                drone.for_back_velocity = -10
                drone.up_down_velocity = 0
                drone.yaw_velocity = 0

            # GO_POS1
            elif dir == Order.GO_POS1:
                # drone.up_down_velocity = 5
                drone.left_right_velocity = 0
                drone.for_back_velocity = 0
                drone.up_down_velocity = 0
                drone.yaw_velocity = 10

            # GO_POS2
            elif dir == Order.GO_POS2:
                # drone.up_down_velocity = 5
                drone.left_right_velocity = 0
                drone.for_back_velocity = 0
                drone.up_down_velocity = 0
                drone.yaw_velocity = -10

            # GO_POS3
            elif dir == Order.GO_POS3:
                # drone.up_down_velocity = -5
                drone.left_right_velocity = 0
                drone.for_back_velocity = 0
                drone.up_down_velocity = 0
                drone.yaw_velocity = -10

            # GO_POS4
            elif dir == Order.GO_POS4:
                # drone.up_down_velocity = -5
                drone.left_right_velocity = 0
                drone.for_back_velocity = 0
                drone.up_down_velocity = 0
                drone.yaw_velocity = 10

            # DO_SEARCH
            elif dir == Order.DO_SEARCH:
                drone.left_right_velocity = 0
                drone.for_back_velocity = 0
                drone.up_down_velocity = 0
                drone.yaw_velocity = 30

            # default
            elif dir == Order.default_mode:
                drone.left_right_velocity = 0
                drone.for_back_velocity = 0
                drone.up_down_velocity = 0
                drone.yaw_velocity = 0

            # SEND VELOCITY VALUES TO TELLO
            if drone.send_rc_control:
                drone.send_rc_control(drone.left_right_velocity, drone.for_back_velocity, drone.up_down_velocity,
                                      drone.yaw_velocity)
            print(dir)
            log_str += str(dir) + '\n'

            stack = stackImages(0.9, ([recognition_area, result], [imgDil, imgContour]))
            cv2.imshow('Horizontal Stacking', stack)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                raise KeyboardInterrupt
        elif my_cam == Cam.WEBCAM:
            ret, frame = cap.read()
            frame_copy = frame.copy()

            img = cv2.resize(frame, (width, height))
            imgContour = img.copy()
            imgHsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            lower = lower_green
            upper = upper_green
            mask = cv2.inRange(imgHsv, lower, upper)
            result = cv2.bitwise_and(img, img, mask=mask)
            mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

            imgBlur = cv2.GaussianBlur(result, (7, 7), 1)
            imgGray = cv2.cvtColor(imgBlur, cv2.COLOR_BGR2GRAY)
            threshold1 = cv2.getTrackbarPos("Threshold1", "Parameters")
            threshold2 = cv2.getTrackbarPos("Threshold2", "Parameters")
            imgCanny = cv2.Canny(imgGray, threshold1, threshold2)
            kernel = np.ones((5, 5))
            imgDil = cv2.dilate(imgCanny, kernel, iterations=1)

            results = model(frame, size=640)
            xyxy = results.pandas().xyxy[0]
            xy_list = []
            for i in range(4):
                xy_list.append(int(xyxy[i].item()))

            getContours(imgDil, imgContour, detect_color, xyxy=xy_list, object_detect=object_detection)
            display(imgContour)

            print(f'dir : {dir}')

            stack = stackImages(0.9, ([img, result], [imgDil, imgContour]))

            cv2.imshow('Main', stack)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


# ?????? ????????? ?????? ????????????
except KeyboardInterrupt:
    print('KeyboardInterrupt ??????. ???????????? ???????????????.')
    log_str += 'KeyboardInterrupt ??????. ???????????? ???????????????.\n'
    log_str += ('time: ' + str(time.time() - start_time) + '\n')
    print(f'????????? ????????? : {drone.get_battery()}')
    log_str += f'????????? ????????? : {drone.get_battery()}\n'
    f.write(log_str)
    f.close()
    drone.land()
    cv2.destroyAllWindows()
