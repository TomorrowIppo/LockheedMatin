from djitellopy import Tello
from enum import Enum, auto
import cv2
import time
import numpy as np
import math


######################################################################
width = 640  # WIDTH OF THE IMAGE
height = 480  # HEIGHT OF THE IMAGE
deadZone = 100

######################################################################

######################################################################
start_time = time.time()
hover_time = 0
init_hover_time = True

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
init_height = True

global detect_G
detect_G = False
QR_G = False

global detect_R
detect_R = False
QR_R = False

global detect_B
detect_B = False
QR_B = False

global searching_mode
searching_mode = False

lower_blue = np.array([101, 50, 38])
upper_blue = np.array([110, 255, 255])

lower_green = np.array([36, 25, 25])
upper_green = np.array([70, 225, 255])

lower_red = np.array([155,25,0])
upper_red = np.array([179,255,255])

f = open("dji_tello_test_log.txt", 'w')
global log_str
log_str = ''
######################################################################

startCounter = True

# CONNECT TO TELLO
# drone = Tello()
# drone.connect()
# drone.for_back_velocity = 0
# drone.left_right_velocity = 0
# drone.up_down_velocity = 0
# drone.yaw_velocity = 0
# drone.speed = 0


# print(drone.get_battery())
# log_str += ('drone_battery : ' + str(drone.get_battery()) + '%\n')
#
# drone.streamoff()
# drone.streamon()
########################

frameWidth = width
frameHeight = height
center_block_area = (frameWidth / 3) * (frameHeight / 3)
# cap = cv2.VideoCapture(1)
# cap.set(3, frameWidth)
# cap.set(4, frameHeight)
# cap.set(10,200)


global imgContour
global dir


# 명령용 enum 클래스
class Order(Enum):
    default_mode = auto()

    GO_LEFT = auto()
    TURN_LEFT = auto()

    GO_RIGHT = auto()
    TURN_RIGHT = auto()

    GO_UP = auto()
    GO_DOWN = auto()

    GO_FORWARD = auto()
    GO_BACKWARD = auto()


def empty(a):
    pass


cv2.namedWindow("HSV")
cv2.resizeWindow("HSV", 640, 240)
cv2.createTrackbar("HUE Min", "HSV", 20, 179, empty)
cv2.createTrackbar("HUE Max", "HSV", 40, 179, empty)
cv2.createTrackbar("SAT Min", "HSV", 148, 255, empty)
cv2.createTrackbar("SAT Max", "HSV", 255, 255, empty)
cv2.createTrackbar("VALUE Min", "HSV", 89, 255, empty)
cv2.createTrackbar("VALUE Max", "HSV", 255, 255, empty)

cv2.namedWindow("Parameters")
cv2.resizeWindow("Parameters", 640, 240)
cv2.createTrackbar("Threshold1", "Parameters", 166, 255, empty)
cv2.createTrackbar("Threshold2", "Parameters", 171, 255, empty)
cv2.createTrackbar("Area", "Parameters", 1750, 30000, empty)


def stackImages(scale, imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range ( 0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape [:2]:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        hor_con = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None,scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(imgArray)
        ver = hor
    return ver


def getContours(img, imgContour, detect_color):
    global dir
    global searching_mode
    global detect_G
    global detect_R
    global detect_B
    global log_str
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if len(contours) != 0 and searching_mode:
        for cnt in contours:
            area = cv2.contourArea(cnt)
            areaMin = cv2.getTrackbarPos("Area", "Parameters")
            if area > areaMin:
                cv2.drawContours(imgContour, cnt, -1, (255, 0, 255), 7)
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                #print(len(approx))
                x , y , w, h = cv2.boundingRect(approx)
                cx = int(x + (w / 2))  # CENTER X OF THE OBJECT
                cy = int(y + (h / 2))  # CENTER Y OF THE OBJECT

                if cx < (int(frameWidth/2)-deadZone):
                    cv2.putText(imgContour, ' TURN LEFT ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    #cv2.rectangle(imgContour, (0, int(frameHeight/2-deadZone)), (int(frameWidth/2)-deadZone, int(frameHeight/2)+deadZone), (0, 0, 255), cv2.FILLED)
                    dir = Order.TURN_LEFT
                elif cx > (int(frameWidth / 2) + deadZone):
                    cv2.putText(imgContour, ' TURN RIGHT ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    #cv2.rectangle(imgContour, (int(frameWidth/2+deadZone), int(frameHeight/2-deadZone)), (frameWidth, int(frameHeight/2)+deadZone), (0, 0, 255), cv2.FILLED)
                    dir = Order.TURN_RIGHT
                elif cy < (int(frameHeight / 2) - deadZone):
                    cv2.putText(imgContour, ' GO UP ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    #cv2.rectangle(imgContour, (int(frameWidth/2-deadZone), 0), (int(frameWidth/2+deadZone), int(frameHeight/2)-deadZone), (0, 0, 255), cv2.FILLED)
                    dir = Order.GO_UP
                elif cy > (int(frameHeight / 2) + deadZone):
                    cv2.putText(imgContour, ' GO DOWN ', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    #cv2.rectangle(imgContour, (int(frameWidth/2-deadZone), int(frameHeight/2)+deadZone), (int(frameWidth/2+deadZone), frameHeight), (0, 0, 255), cv2.FILLED)
                    dir = Order.GO_DOWN
                else:
                    if ((center_block_area - 1000) <= area) and (area <= (center_block_area + 1000)):
                        dir = Order.default_mode
                        if detect_color == 'G':
                            print('G 중심 영역 도달')
                            log_str += 'G 중심 영역 도달\n'
                            print(f'Area : {area}')
                            log_str += f'Area : {area}\n'
                            detect_G = True
                        elif detect_color == 'R':
                            print('R 중심 영역 도달')
                            log_str += 'R 중심 영역 도달\n'
                            print(f'Area : {area}')
                            log_str += f'Area : {area}\n'
                            detect_R = True
                        elif detect_color == 'B':
                            print('B 중심 영역 도달')
                            log_str += 'B 중심 영역 도달\n'
                            print(f'Area : {area}')
                            log_str += f'Area : {area}\n'
                            detect_B = True

                    elif area > center_block_area + 2000:
                        dir = Order.GO_BACKWARD
                        print('기준치보다 큼')
                        log_str += '기준치보다 큼\n'
                    elif area < center_block_area - 2000:
                        dir = Order.GO_FORWARD
                        print('기준치보다 작음')
                        log_str += '기준치보다 작음\n'
                    else:
                        pass

                cv2.line(imgContour, (int(frameWidth/2), int(frameHeight/2)), (cx, cy),(0, 0, 255), 3)
                cv2.rectangle(imgContour, (x, y), (x + w, y + h), (0, 255, 0), 5)
                cv2.putText(imgContour, "Points: " + str(len(approx)), (x + w + 20, y + 20), cv2.FONT_HERSHEY_COMPLEX, .7, (0, 255, 0), 2)
                cv2.putText(imgContour, "Area: " + str(int(area)), (x + w + 20, y + 45), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(imgContour, " " + str(int(x)) + " " + str(int(y)), (x - 20, y - 45), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 0), 2)
            else:
                dir = Order.default_mode
    elif searching_mode:
        dir = Order.TURN_LEFT
    else:
        dir = Order.default_mode


def display(img):
    cv2.line(img, (int(frameWidth/2)-deadZone, 0), (int(frameWidth/2)-deadZone, frameHeight), (255, 255, 0), 3)
    cv2.line(img, (int(frameWidth/2)+deadZone, 0), (int(frameWidth/2)+deadZone, frameHeight), (255, 255, 0), 3)
    cv2.circle(img, (int(frameWidth/2), int(frameHeight/2)), 5, (0, 0, 255), 5)
    cv2.line(img, (0, int(frameHeight / 2) - deadZone), (frameWidth, int(frameHeight / 2) - deadZone), (255, 255, 0), 3)
    cv2.line(img, (0, int(frameHeight / 2) + deadZone), (frameWidth, int(frameHeight / 2) + deadZone), (255, 255, 0), 3)


def QR(img):
    global log_str
    global start_hover
    global QR_hover_detect
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
            return True

    return False


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


def do_action(num):
    if num == 1:
        pass
    elif num == 2:
        pass
    elif num == 3:
        pass
    elif num == 4:
        pass
    elif num == 5:
        pass
    else:
        pass


try:
    cap = cv2.VideoCapture(0)
    init_height = False
    while True:
        # GET THE IMAGE FROM TELLO
        # frame_read = drone.get_frame_read()
        ret, myFrame = cap.read()
        img = cv2.resize(myFrame, (width, height))
        imgContour = img.copy()
        imgHsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # drone_height = drone.get_height()

        h_min = cv2.getTrackbarPos("HUE Min","HSV")
        h_max = cv2.getTrackbarPos("HUE Max", "HSV")
        s_min = cv2.getTrackbarPos("SAT Min", "HSV")
        s_max = cv2.getTrackbarPos("SAT Max", "HSV")
        v_min = cv2.getTrackbarPos("VALUE Min", "HSV")
        v_max = cv2.getTrackbarPos("VALUE Max", "HSV")

        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])

        detect_color = None

        # takeoff
        # if startCounter:
        #     drone.takeoff()
        #     startCounter = False

        # 0단계, 고도 초기화 단계
        if init_height:
            pass
            # print(drone_height)
            # if drone_height == 70:
            #     init_height = False
            #     print('------ 고도 초기화 종료 ------')
            #     log_str += '------ 고도 초기화 종료 ------\n'
            #
            # elif drone_height < 70:
            #     dir = Order.GO_UP
            # else:
            #     dir = Order.GO_DOWN
        else:
            # 1단계, 'hover' QR 탐색
            if not QR_hover_detect:
                print('1단계 : hover QR 탐색중')
                log_str += '1단계 : hover QR 탐색중\n'
                qrDecoder = cv2.QRCodeDetector()

                # hover QR을 찾는 중
                QR(img)

            # 1.5단계, 'hover' QR 탐지 시 호버링
            if start_hover:
                if init_hover_time:
                    print('호버링 시작')
                    log_str += '호버링 시작\n'
                    hover_time = time.time()
                    init_hover_time = False
                    dir = Order.default_mode
                interval = time.time() - hover_time
                if (5.0 <= interval) and (interval <= 5.1):
                    start_hover = False
                    searching_mode = True
                    print(f'호버링 끝, interval : {interval}')
                    log_str += f'호버링 끝, interval : {interval}\n'

            # 2단계, G R B 탐색 및 QR 인식 후 미션 수행 단계
            if QR_hover_detect and not start_hover:
                print('2단계 : 현재 ', end='')
                log_str += '2단계 : 현재 '
                # Green 탐색 단계
                if not detect_G:
                    print('Green 탐색 중')
                    log_str += 'Green 탐색 중\n'
                    lower = lower_green
                    upper = upper_green
                    detect_color = 'G'

                # Green에 접근했지만, QR을 못 읽었을 때
                if detect_G and not QR_G:
                    # QR을 찾는 중
                    if QR(img):
                        QR_G = True

                # Green 탐색 후 Red 탐색 단계
                if detect_G and not detect_R and QR_G:
                    print('Red 탐색 중')
                    log_str += 'Red 탐색 중\n'
                    lower = lower_red
                    upper = upper_red
                    detect_color = 'R'

                # Red에 접근했지만, QR을 못 읽었을 때
                if detect_G and detect_R and not QR_R:
                    # QR을 찾는 중
                    if QR(img):
                        QR_R = True

                # Green, Red 탐색 후 Blue 탐색 단계
                if detect_G and detect_R and not detect_B and QR_G and QR_R:
                    print('Blue 탐색 중')
                    log_str += 'Blue 탐색 중\n'
                    lower = lower_blue
                    upper = upper_blue
                    detect_color = 'B'

                # Blue에 접근했지만, QR을 못 읽었을 때
                if detect_G and detect_R and detect_B and not QR_B:
                    # QR을 찾는 중
                    if QR(img):
                        QR_B = True

                # G, B, R의 QR을 모두 감지 시 강제 종료
                if QR_G and QR_R and QR_B:
                    raise KeyboardInterrupt

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

        getContours(imgDil, imgContour, detect_color)
        display(imgContour)


        # GO_LEFT
        if dir == Order.GO_LEFT:
            log = 'drone.left_right_velocity = -60'
            print(log)
        # TURN_LEFT
        elif dir == Order.TURN_LEFT:
            log = 'drone.yaw_velocity = -60'
            print(log)
        # GO_RIGHT
        elif dir == Order.GO_RIGHT:
            log = 'drone.left_right_velocity = 60'
            print(log)
        # TURN_RIGHT
        elif dir == Order.TURN_LEFT:
            log = 'drone.yaw_velocity = 60'
            print(log)
        # GO_UP
        elif dir == Order.GO_UP:
            log = 'drone.up_down_velocity = 60'
            print(log)
        # GO_DOWN
        elif dir == Order.GO_DOWN:
            log = 'drone.up_down_velocity = -60'
            print(log)
        # GO_FORWARD
        elif dir == Order.GO_FORWARD:
            log = 'drone.for_back_velocity = 60'
            print(log)
        # GO_BACKWARD
        elif dir == Order.GO_BACKWARD:
            log = 'drone.for_back_velocity = -60'
            print(log)
        # default
        elif dir == Order.default_mode:
            # drone.left_right_velocity = 0
            # drone.for_back_velocity = 0
            # drone.up_down_velocity = 0
            # drone.yaw_velocity = 0
            print('default')

       # SEND VELOCITY VALUES TO TELLO
       #  if drone.send_rc_control:
       #      drone.send_rc_control(drone.left_right_velocity, drone.for_back_velocity, drone.up_down_velocity, drone.yaw_velocity)
        print(dir)

        stack = stackImages(0.9, ([img, result], [imgDil, imgContour]))
        cv2.imshow('Horizontal Stacking', stack)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            raise KeyboardInterrupt

# 강제 종료에 대한 예외처리
except KeyboardInterrupt:
    print('KeyboardInterrupt 발생. 프로그램 종료합니다.')
    log_str += 'KeyboardInterrupt 발생. 프로그램 종료합니다.\n'
    log_str += ('time: ' + str(time.time() - start_time) + '\n')
    f.write(log_str)
    f.close()
    # drone.land()
    cv2.destroyAllWindows()