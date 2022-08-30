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

red_captured = False
green_captured = False
blue_captured = False

init_DRONE_SPEED_Y = 10
default_DRONE_SPEED_Y = 13
slow_DRON_SPEED_Y = 7
DRONE_ROTATE_SPEED = 70

# 캡쳐 interval
capture_wait = False
capture_wait_check_mode = False
start_caputre_count = 0
caputer_interval = 0

hover_MODE = False
hover_Check_mode = False
start_hover = 0
interval = 0

DRONE_UP_MODE = True
init_height = True

lower_blue = np.array([100, 150, 0])
upper_blue = np.array([140, 255, 255])

lower_green = np.array([50, 150, 50])  # 초록색 범위
upper_green = np.array([80, 255, 255])

# lower_red = np.array([0, 100, 100])
# upper_red = np.array([7, 255, 255])

lower_red = np.array([0, 50, 50])
upper_red = np.array([10, 255, 255])

drone = Tello()
drone.connect()
print(drone.get_battery())
log_str += ('drone_battery : ' + str(drone.get_battery()) + '%\n')
drone.takeoff()

drone.streamon()

# 데이터 로그
file = '/LockheadMartin/1st_qualification/DJI_Tello_Log/'
f = open(file + "dji_tello_main_log.txt", 'w')

try:
    while True:
        # drone.send_rc_control에 전달할 변수
        up_down_velocity = 0
        right_left_velocity = 0
        yaw_velocity = 0

        # up_down_velocity 값 제어에 사용할 변수
        DRONE_SPEED_Y = 0

        # 드론 고도
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

        # 메인 탐색
        if red_detect and not hover_Check_mode and not hover_MODE:
            # 파랑 혹은 초록이 감지 됐을 때, QR 파트 진입
            if blue_detect or green_detect:
                print('QR 진입')
                log_str += ('QR 진입\n')
                # QR Start
                #inputImage = cv2.resize(frame, None, fx=0.2, fy=0.2, interpolation=cv2.INTER_AREA)

                qrDecoder = cv2.QRCodeDetector()

                # QR코드를 찾고 디코딩, 정상적인 종료 지점
                data, bbox, rectifiedImage = qrDecoder.detectAndDecode(frame)
                if len(data) > 0:
                    print("Decoded Data : {}".format(data))
                    log_str += ("Decoded Data : {}".format(data) + '\n')
                    rectifiedImage = np.uint8(rectifiedImage)
                    log_str += ('time: ' + str(time.time() - start_time))
                    f.write(log_str)
                    f.close()
                    break
                else:
                    # 탐색 파트
                    print(drone_height)
                    DRONE_SPEED_Y = default_DRONE_SPEED_Y

                    if drone_height < 40:
                        DRONE_UP_MODE = True
                        # DRONE_SPEED_Y = default_DRONE_SPEED_Y
                        yaw_velocity = DRONE_ROTATE_SPEED
                    elif drone_height > 70:
                        DRONE_UP_MODE = False
                        # DRONE_SPEED_Y = default_DRONE_SPEED_Y
                        yaw_velocity = DRONE_ROTATE_SPEED

                    if 40 < drone_height and drone_height < 50:
                        DRONE_SPEED_Y = slow_DRON_SPEED_Y

                    if 60 < drone_height and drone_height < 70:
                        DRONE_SPEED_Y = slow_DRON_SPEED_Y

                    if DRONE_UP_MODE:
                        up_down_velocity = DRONE_SPEED_Y
                    else:
                        up_down_velocity = -DRONE_SPEED_Y
                # QR End

            # 파, 초 파트
            else:
                # 고도 70으로 초기화
                if init_height:
                    print('init 중')
                    log_str += 'init 중\n'
                    if drone_height == 70:
                        init_height = False
                        DRONE_UP_MODE = False
                        print('고도 70 도달, 고도 초기화 종료')
                        log_str += ('고도 70 도달, 고도 초기화 종료\n')
                    elif drone_height < 70:
                        DRONE_SPEED_Y = init_DRONE_SPEED_Y
                    else:
                        DRONE_SPEED_Y = -init_DRONE_SPEED_Y

                    if DRONE_UP_MODE:
                        up_down_velocity = DRONE_SPEED_Y
                    else:
                        up_down_velocity = -DRONE_SPEED_Y
                # 파, 초 탐색 파트
                else:
                    # Green and Blue
                    print('Green_Blue 탐색 진입')
                    log_str += ('Green_Blue 탐색 진입\n')
                    contours1, hierarchy1 = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    contours2, hierarchy2 = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    # 탐색 파트
                    print(drone_height)

                    DRONE_SPEED_Y = default_DRONE_SPEED_Y

                    if drone_height < 40:
                        DRONE_UP_MODE = True
                        DRONE_SPEED_Y = default_DRONE_SPEED_Y
                        yaw_velocity = DRONE_ROTATE_SPEED
                    elif drone_height > 70:
                        DRONE_UP_MODE = False
                        DRONE_SPEED_Y = default_DRONE_SPEED_Y
                        yaw_velocity = DRONE_ROTATE_SPEED

                    if 40 < drone_height and drone_height < 50:
                        DRONE_SPEED_Y = slow_DRON_SPEED_Y

                    if 60 < drone_height and drone_height < 70:
                        DRONE_SPEED_Y = slow_DRON_SPEED_Y

                    if DRONE_UP_MODE:
                        up_down_velocity = DRONE_SPEED_Y
                    else:
                        up_down_velocity = -DRONE_SPEED_Y

                    if len(contours1) == 0 and len(contours2) == 0 and not capture_wait:
                        pass

                    elif capture_wait:
                        if capture_wait_check_mode:
                            print('캡쳐 대기 진행중.')
                            log_str += '캡쳐 대기 진행중.\n'
                            start_caputre_count = time.time()
                            log_str += 'capture_wating_start_time : ' + str(start_caputre_count) + '\n'
                            capture_wait_check_mode = False
                        capture_interval = (time.time() - start_caputre_count)
                        if 1.0 <= capture_interval and capture_interval <= 1.1:
                            print('캡쳐 대기 끝')
                            log_str += '캡쳐 대기 끝\n'
                            log_str += 'capture_wating_end_time : ' + str(capture_interval) + '\n'
                            capture_wait = False
                            if len(contours1) == 0 and len(contours2) == 0:
                                capture_wait = True
                                capture_wait_check_mode = True
                            else:
                                if len(contours1) != 0:
                                    for contour in contours1:
                                        if cv2.contourArea(contour) > 500:
                                            x, y, w, h = cv2.boundingRect(contour)
                                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                                            if not green_detect:
                                                green_detect = True
                                                capture_wait = True
                                                capture_wait_check_mode = True
                                                print("초록 감지")
                                                log_str += ('초록 감지\n')
                                                green_detect_img = cv2.imwrite('green_detect_img.png', frame)

                                if len(contours2) != 0:
                                    for contour in contours2:
                                        if cv2.contourArea(contour) > 500:
                                            x, y, w, h = cv2.boundingRect(contour)
                                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                                            if not blue_detect:
                                                blue_detect = True
                                                capture_wait = True
                                                capture_wait_check_mode = True
                                                print("파랑 감지")
                                                log_str += ('파랑 감지\n')
                                                blue_detect_img = cv2.imwrite('blue_detect_img.png', frame)

                    else:
                        if len(contours1) != 0:
                            for contour in contours1:
                                if cv2.contourArea(contour) > 500:
                                    x, y, w, h = cv2.boundingRect(contour)
                                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                                    if not green_detect:
                                        #green_detect = True
                                        capture_wait = True
                                        capture_wait_check_mode = True
                                        print("초록 감지")
                                        log_str += ('초록 감지\n')
                                        #green_detect_img = cv2.imwrite('green_detect_img.png', frame)

                        if len(contours2) != 0:
                            for contour in contours2:
                                if cv2.contourArea(contour) > 500:
                                    x, y, w, h = cv2.boundingRect(contour)
                                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                                    if not blue_detect:
                                        #blue_detect = True
                                        capture_wait = True
                                        capture_wait_check_mode = True
                                        print("파랑 감지")
                                        log_str += ('파랑 감지\n')
                                        #blue_detect_img = cv2.imwrite('blue_detect_img.png', frame)

        # 3초 호버링 파트
        elif hover_MODE:
            if hover_Check_mode:
                print('호버링 진행중.')
                log_str += '호버링 진행중.\n'
                start_hover = time.time()
                log_str += 'hovering_start_time : ' + str(start_hover) + '\n'
                hover_Check_mode = False
            interval = (time.time() - start_hover)
            if 5.0 <= interval and interval <= 5.1:
                print('호버링 끝')
                log_str += '호버링 끝\n'
                log_str += 'hovering_end_time : ' + str(interval) + '\n'
                hover_MODE = False

        # 빨강 탐색 파트
        else:
            print('빨강 탐색')
            log_str += ('빨강 탐색\n')
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) != 0:
                for contour in contours:
                    if cv2.contourArea(contour) > 500:
                        x, y, w, h = cv2.boundingRect(contour)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                        if not red_detect:
                            red_detect = True
                            hover_MODE = True
                            hover_Check_mode = True
                            print('빨강 감지')
                            log_str += ('빨강 감지\n')
                            red_detect_img = cv2.imwrite('red_detect_img.png', frame)
                            red_captured = True
                    else:
                        pass

        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) != 0:
            for contour in contours:
                if cv2.contourArea(contour) > 500:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)


        contours1, hierarchy1 = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours1) != 0:
            for contour in contours1:
                if cv2.contourArea(contour) > 500:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)


        contours2, hierarchy2 = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours2) != 0:
            for contour in contours2:
                if cv2.contourArea(contour) > 500:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)


        drone.send_rc_control(right_left_velocity, 0, up_down_velocity, yaw_velocity)
        log_str += (f'[{right_left_velocity}, 0, {up_down_velocity}, {yaw_velocity}]')
        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # quit from script
            break

    drone.land()
    cv2.destroyAllWindows()


# 강제종료 했을 때, 안전하게 마무리
except KeyboardInterrupt:
    print('KeyboardInterrupt 발생. 프로그램 종료합니다.')
    log_str += ('KeyboardInterrupt 발생. 프로그램 종료합니다.\n')
    log_str += ('time: ' + str(time.time() - start_time) + '\n')
    f.write(log_str)
    f.close()
    drone.land()
    cv2.destroyAllWindows()