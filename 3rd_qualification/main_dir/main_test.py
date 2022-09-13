from djitellopy import Tello
import Utils
from enum import Enum, auto
import numpy as np
import cv2
import time

# --------------------------------------------------------------------

width = 640  # WIDTH OF THE IMAGE
height = 480  # HEIGHT OF THE IMAGE
deadZone = 60

# --------------------------------------------------------------------


# --------------------------------------------------------------------

start_time = time.time()
hover_time = 0
init_hover_time = True
global init_QR_height
init_QR_height = False
global QR_height_1
QR_height_1 = False
global QR_height_2
QR_height_2 = False

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
QR_G = False

global detect_R
detect_R = False
QR_R = False

global detect_B
detect_B = False
QR_B = False

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

lower_green = np.array([56, 145, 1])
upper_green = np.array([76, 165, 81])

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


# drone, web_cam 구분용 클래스, 변수
class Cam(Enum):
    DRONE = auto()
    WEBCAM = auto()
my_cam = Cam.WEBCAM


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

color = None
detect_color = None
cap = None
drone = None
if my_cam == Cam.WEBCAM:
    cap = cv2.VideoCapture(0)
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

try:
    while True:
        if my_cam == Cam.DRONE:
            # GET THE IMAGE FROM TELLO
            frame_read = drone.get_frame_read()
            myFrame = frame_read.frame

            img = cv2.resize(myFrame, (width, height))
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

            # 0단계, 고도 초기화 단계
            if init_height and not startCounter:
                print(f'------ 고도 초기화 중 ({drone_height}) ------')
                log_str += f'------ 고도 초기화 중 ({drone_height}) ------\n'
                if drone_height == 60:
                    init_height = False
                    print('------ 고도 초기화 종료 ------')
                    log_str += '------ 고도 초기화 종료 ------\n'
                    if QR_hover_detect:
                        drone.move_right(20)
                        searching_mode = True

                elif drone_height < 60:
                    dir = Order.GO_UP
                else:
                    dir = Order.GO_DOWN
            else:
                # 1단계, 'hover' QR 탐색
                if not QR_hover_detect:
                    print('1단계 : hover QR 탐색중')
                    log_str += '1단계 : hover QR 탐색중\n'
                    qrDecoder = cv2.QRCodeDetector()

                    # hover QR을 찾는 중
                    data, bbox, rectifiedImage = qrDecoder.detectAndDecode(img)
                    if len(data) > 0 and data == 'hover':
                        print("Decoded Data : {}".format(data))
                        log_str += f'Decoded Data : {data}\n'
                        rectifiedImage = np.uint8(rectifiedImage)
                        start_hover = True
                        QR_hover_detect = True

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
                        print(f'호버링 끝, interval : {interval}')
                        log_str += f'호버링 끝, interval : {interval}\n'

                # 2단계, G R B 탐색 및 QR 인식 후 미션 수행 단계
                if QR_hover_detect and not start_hover:
                    searching_mode = True
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
                        searching_mode = False
                        if init_QR_height:
                            print(f'------ 고도 초기화 중 ({drone_height}) ------')
                            log_str += f'------ 고도 초기화 중 ({drone_height}) ------\n'
                            if drone_height == 50:
                                init_QR_height = False
                                print('------ 고도 초기화 종료 ------')
                                log_str += '------ 고도 초기화 종료 ------\n'

                            elif drone_height < 50:
                                dir = Order.GO_UP
                            else:
                                dir = Order.GO_DOWN
                        # QR을 찾는 중
                        if Utils.QR(img) is not None:
                            QR_G = True
                            init_height = False
                            Utils.do_action(qr_data)
                            searching_mode = False

                    # Green 탐색 후 Red 탐색 단계
                    if detect_G and not detect_R and QR_G:
                        print('Red 탐색 중')
                        log_str += 'Red 탐색 중\n'
                        lower = lower_red
                        upper = upper_red
                        detect_color = 'R'

                    # Red에 접근했지만, QR을 못 읽었을 때
                    if detect_G and detect_R and not QR_R:
                        searching_mode = False
                        if init_QR_height:
                            print(f'------ 고도 초기화 중 ({drone_height}) ------')
                            log_str += f'------ 고도 초기화 중 ({drone_height}) ------\n'
                            if drone_height == 50:
                                init_QR_height = False
                                print('------ 고도 초기화 종료 ------')
                                log_str += '------ 고도 초기화 종료 ------\n'

                            elif drone_height < 50:
                                dir = Order.GO_UP
                            else:
                                dir = Order.GO_DOWN
                        # QR을 찾는 중
                        if Utils.QR(img) is not None:
                            QR_R = True
                            init_height = False
                            Utils.do_action(qr_data)
                            searching_mode = False

                    # Green, Red 탐색 후 Blue 탐색 단계
                    if detect_G and detect_R and not detect_B and QR_G and QR_R:
                        print('Blue 탐색 중')
                        log_str += 'Blue 탐색 중\n'
                        lower = lower_blue
                        upper = upper_blue
                        detect_color = 'B'

                    # Blue에 접근했지만, QR을 못 읽었을 때
                    if detect_G and detect_R and detect_B and not QR_B:
                        searching_mode = False
                        if init_QR_height:
                            print(f'------ 고도 초기화 중 ({drone_height}) ------')
                            log_str += f'------ 고도 초기화 중 ({drone_height}) ------\n'
                            if drone_height == 50:
                                init_QR_height = False
                                print('------ 고도 초기화 종료 ------')
                                log_str += '------ 고도 초기화 종료 ------\n'

                            elif drone_height < 50:
                                dir = Order.GO_UP
                            else:
                                dir = Order.GO_DOWN
                        # QR을 찾는 중
                        if Utils.QR(img) is not None:
                            QR_B = True
                            init_height = False
                            Utils.do_action(qr_data)
                            searching_mode = False

                    # G, B, R의 QR을 모두 감지 시 강제 종료
                    if QR_G and QR_R and QR_B:
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

            Utils.getContours(imgDil, imgContour, color, detect_color, init_QR_height, log_str, searching_mode, dir)
            Utils.display(imgContour)

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

            # drone.left_right_velocity = -5
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

            # drone.left_right_velocity = 5
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

            stack = Utils.stackImages(0.9, ([img, result], [imgDil, imgContour]))
            cv2.imshow('Horizontal Stacking', stack)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                raise KeyboardInterrupt
        elif my_cam == Cam.WEBCAM:
            ret, frame = cap.read()

            img = cv2.resize(frame, (width, height))
            imgContour = img.copy()
            imgHsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            h_min = cv2.getTrackbarPos("HUE Min", "HSV")
            h_max = cv2.getTrackbarPos("HUE Max", "HSV")
            s_min = cv2.getTrackbarPos("SAT Min", "HSV")
            s_max = cv2.getTrackbarPos("SAT Max", "HSV")
            v_min = cv2.getTrackbarPos("VALUE Min", "HSV")
            v_max = cv2.getTrackbarPos("VALUE Max", "HSV")

            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
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
            Utils.getContours(imgDil, imgContour, color, detect_color, init_QR_height, log_str, searching_mode, dir)
            Utils.display(imgContour)

            print(dir)

            stack = Utils.stackImages(0.9, ([img, result], [imgDil, imgContour]))
            cv2.imshow('Main', stack)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


# 강제 종료에 대한 예외처리
except KeyboardInterrupt:
    print('KeyboardInterrupt 발생. 프로그램 종료합니다.')
    log_str += 'KeyboardInterrupt 발생. 프로그램 종료합니다.\n'
    log_str += ('time: ' + str(time.time() - start_time) + '\n')
    print(f'베터리 잔여량 : {drone.get_battery()}')
    log_str += f'베터리 잔여량 : {drone.get_battery()}\n'
    f.write(log_str)
    f.close()
    drone.land()
    cv2.destroyAllWindows()
