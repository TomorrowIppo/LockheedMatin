import cv2
import sys
import os.path
from djitellopy import Tello
import numpy as np
import time

# 로그할 데이터를 담을 문자열
log_str = ''

# 실행 시간을 위한 것
start_time = time.time()

red_detect = False
blue_detect = False
green_detect = False
qr_detect = False

TOLERANCE_X = 5
TOLERANCE_Y = 5
SLOWDOWN_THRESHOLD_X = 20
SLOWDOWN_THRESHOLD_Y = 20
DRONE_SPEED_X = 20
init_DRONE_SPEED_Y = 10
default_DRONE_SPEED_Y = 15
slow_DRON_SPEED_Y = 10
DRONE_DIR_Y = 1
DRONE_ROTATE_SPEED = 75
SET_POINT_X = 960 / 2
SET_POINT_Y = 720 / 2

DRONE_UP_MODE = True
init_height = True

lower_blue = np.array([100, 100, 120])  # 파랑색 범위
upper_blue = np.array([150, 255, 255])

lower_green = np.array([50, 150, 50])  # 초록색 범위
upper_green = np.array([80, 255, 255])

lower_red = np.array([0, 50, 50])  # 빨간색 범위
upper_red = np.array([10, 255, 255])

drone = Tello()  # declaring drone object
drone.connect()
print(drone.get_battery())
log_str += ('drone_battery : ' + str(drone.get_battery()) + '%\n')
#drone.takeoff()

drone.streamon()  # start camera streaming

# 데이터 로그
file = '/LockheadMartin/1st_qualification/DJI_Tello_Log/'
f = open(file + "dji_tello_main_log.txt", 'w')

try:
    while True:
        up_down_velocity = 0
        right_left_velocity = 0
        yaw_velocity = 0
        DRONE_SPEED_Y = 0
        drone_height = drone.get_height()

        frame = drone.get_frame_read().frame

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Threshold the HSV image to get only blue colors
        mask = cv2.inRange(hsv, lower_red, upper_red)  # 110<->150 Hue(색상) 영역을 지정.
        mask1 = cv2.inRange(hsv, lower_green, upper_green)  # 영역 이하는 모두 날림 검정. 그 이상은 모두 흰색 두개로 Mask를 씌움.
        mask2 = cv2.inRange(hsv, lower_blue, upper_blue)

        # Bitwise-AND mask and original image
        res = cv2.bitwise_and(frame, frame, mask=mask)  # 흰색 영역에 파랑색 마스크를 씌워줌.
        res1 = cv2.bitwise_and(frame, frame, mask=mask1)  # 흰색 영역에 초록색 마스크를 씌워줌.
        res2 = cv2.bitwise_and(frame, frame, mask=mask2)  # 흰색 영역에 빨강색 마스크를 씌워줌.

        # Red
        if red_detect:
            if blue_detect or green_detect:
                print('QR 진입')
                log_str += ('QR 진입\n')
                # QR Start
                inputImage = cv2.resize(frame, None, fx=0.2, fy=0.2, interpolation=cv2.INTER_AREA)

                qrDecoder = cv2.QRCodeDetector()

                # QR코드를 찾고 디코드해줍니다, 정상적인 종료 지점
                data, bbox, rectifiedImage = qrDecoder.detectAndDecode(inputImage)
                if len(data) > 0:
                    print("Decoded Data : {}".format(data))
                    log_str += ('"Decoded Data : {}".format(data)\n')
                    rectifiedImage = np.uint8(rectifiedImage)
                    log_str += ('time: ' + str(time.time() - start_time))
                    f.write(log_str)
                    f.close()
                    break
                else:
                    DRONE_SPEED_Y = default_DRONE_SPEED_Y

                    if drone_height < 40:
                        DRONE_UP_MODE = True
                        # DRONE_SPEED_Y = default_DRONE_SPEED_Y
                        yaw_velocity = DRONE_ROTATE_SPEED
                    elif drone_height > 80:
                        DRONE_UP_MODE = False
                        # DRONE_SPEED_Y = default_DRONE_SPEED_Y
                        yaw_velocity = DRONE_ROTATE_SPEED

                    if 40 < drone_height and drone_height < 50:
                        DRONE_SPEED_Y = slow_DRON_SPEED_Y

                    if 70 < drone_height and drone_height < 80:
                        DRONE_SPEED_Y = slow_DRON_SPEED_Y

                    if DRONE_UP_MODE:
                        up_down_velocity = DRONE_SPEED_Y
                    else:
                        up_down_velocity = -DRONE_SPEED_Y
                # QR End
            else:
                print('Green_Blue 진입')
                log_str += ('Green_Blue 진입\n')
                # 고도 80으로 설정
                if init_height:
                    if drone_height == 80:
                        init_height = False
                        DRONE_UP_MODE = False
                        print('고도 80 도달, 고도 초기화 종료')
                        log_str += ('고도 80 도달, 고도 초기화 종료\n')
                    elif drone_height < 80:
                        DRONE_SPEED_Y = init_DRONE_SPEED_Y
                    else:
                        DRONE_SPEED_Y = -init_DRONE_SPEED_Y

                    if DRONE_UP_MODE:
                        up_down_velocity = DRONE_SPEED_Y
                    else:
                        up_down_velocity = -DRONE_SPEED_Y
                else:
                    # Green and Blue
                    contours1, hierarchy1 = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    contours2, hierarchy2 = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    if len(contours1) == 0 and len(contours2) == 0:
                        #print('아직 못 찾음')
                        #print(drone_height)

                        DRONE_SPEED_Y = default_DRONE_SPEED_Y

                        if drone_height < 40:
                            DRONE_UP_MODE = True
                            #DRONE_SPEED_Y = default_DRONE_SPEED_Y
                            yaw_velocity = DRONE_ROTATE_SPEED
                        elif drone_height > 80:
                            DRONE_UP_MODE = False
                            #DRONE_SPEED_Y = default_DRONE_SPEED_Y
                            yaw_velocity = DRONE_ROTATE_SPEED

                        if 40 < drone_height and drone_height < 50:
                            DRONE_SPEED_Y = slow_DRON_SPEED_Y

                        if 70 < drone_height and drone_height < 80:
                            DRONE_SPEED_Y = slow_DRON_SPEED_Y

                        if DRONE_UP_MODE:
                            up_down_velocity = DRONE_SPEED_Y
                        else:
                            up_down_velocity = -DRONE_SPEED_Y

                    else:
                        if len(contours1) != 0:
                            for contour in contours1:
                                if cv2.contourArea(contour) > 1000:
                                    x, y, w, h = cv2.boundingRect(contour)
                                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                                    if green_detect is False:
                                        green_detect = True
                                        print("초록 감지")
                                        log_str += ('초록 감지\n')
                                        green_detect_img = cv2.imwrite('green_detect_img.png', frame)

                        if len(contours2) != 0:
                            for contour in contours2:
                                if cv2.contourArea(contour) > 1000:
                                    x, y, w, h = cv2.boundingRect(contour)
                                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                                    if blue_detect is False:
                                        blue_detect = True
                                        print("파랑 감지")
                                        log_str += ('파랑 감지\n')
                                        blue_detect_img = cv2.imwrite('blue_detect_img.png', frame)
        else:
            print('빨강 탐색')
            log_str += ('빨강 탐색\n')
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) != 0:
                for contour in contours:
                    if cv2.contourArea(contour) > 1000:
                        x, y, w, h = cv2.boundingRect(contour)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                        if not red_detect:
                            red_detect = True
                            print('빨강 감지')
                            log_str += ('빨강 감지')
                            time.sleep(3)
                            red_detect_img = cv2.imwrite('red_detect_img.png', frame)
                    else:
                        pass

        #drone.send_rc_control(right_left_velocity, 0, up_down_velocity, yaw_velocity)
        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # quit from script
            break

    #drone.land()
    cv2.destroyAllWindows()

except KeyboardInterrupt:
    print('KeyboardInterrupt 발생. 프로그램 종료합니다.')
    log_str += ('KeyboardInterrupt 발생. 프로그램 종료합니다.\n')
    log_str += ('time: ' + str(time.time() - start_time))
    f.write(log_str)
    f.close()
    #drone.land()
    cv2.destroyAllWindows()