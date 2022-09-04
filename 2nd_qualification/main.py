from djitellopy import tello
import numpy as np
import time
import cv2

QR_hover_detect = False
start_hover = False
init_height = True

detect_G = False
QR_G = False

detect_R = False
QR_R = False

detect_B = False
QR_B = False

dir = '/Users/kbj/PycharmProjects/opencv_study/LockheadMartin/2nd_qualification/DJITello_Log/'
f = open("dji_tello_main_log.txt", 'w')
log_str = ''

default_drone_up_down = 10
slow_drone_up_down = 5
default_drone_right_left = 10
slow_drone_right_left = 5
default_drone_forward_backward = 10
slow_drone_forward_backward = 5
default_drone_yaw = 30
slow_drone_yaw = 5

lower_blue = np.array([100, 150, 0])
upper_blue = np.array([140, 255, 255])

lower_green = np.array([50, 150, 50])
upper_green = np.array([80, 255, 255])

lower_red = np.array([0, 50, 50])
upper_red = np.array([10, 255, 255])

drone = tello.Tello()
drone.connect()
print(drone.get_battery())
log_str += ('drone_battery : ' + str(drone.get_battery()) + '%\n')

drone.streamon()

drone.takeoff()

start_time = time.time()
hover_time = 0
init_hover_time = True


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

try:
    while True:
        # drone.send_rc_control에 전달할 변수
        left_right_velocity = 0
        forward_backward_velocity = 0
        up_down_velocity = 0
        yaw_velocity = 0
        drone_height = drone.get_height()

        frame = drone.get_frame_read().frame

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Threshold the HSV image to get only blue colors
        mask_R = cv2.inRange(hsv, lower_red, upper_red)  # 110<->150 Hue(색상) 영역을 지정.
        mask_G = cv2.inRange(hsv, lower_green, upper_green)  # 영역 이하는 모두 날림 검정. 그 이상은 모두 흰색 두개로 Mask를 씌움.
        mask_B = cv2.inRange(hsv, lower_blue, upper_blue)

        # 0단계, 고도 초기화 단계
        if init_height:
            print(drone_height)
            if drone_height == 70:
                init_height = False
                print('------ 고도 초기화 종료 ------')
                log_str += '------ 고도 초기화 종료 ------\n'

            elif drone_height < 70:
                up_down_velocity = default_drone_up_down
            else:
                up_down_velocity = -default_drone_up_down

        else:
            # 1단계, 'hover' QR 탐색
            if not QR_hover_detect:
                print('1단계 : hover QR 탐색중')
                log_str += '1단계 : hover QR 탐색중\n'
                qrDecoder = cv2.QRCodeDetector()

                # hover QR을 찾는 중
                data, bbox, rectifiedImage = qrDecoder.detectAndDecode(frame)
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
                interval = time.time() - hover_time
                if (5.0 <= interval) and (interval <= 5.1):
                    start_hover = False
                    print(f'호버링 끝, interval : {interval}')
                    log_str += f'호버링 끝, interval : {interval}\n'

            # 2단계, G R B 탐색 및 QR 인식 후 미션 수행 단계
            if QR_hover_detect and not start_hover:
                print('2단계 : 현재 ', end='')
                log_str += '2단계 : 현재 '
                yaw_velocity = default_drone_yaw
                # Green 탐색 단계
                if not detect_G:
                    print('Green 탐색 중')
                    log_str += 'Green 탐색 중\n'
                    contours, hierarchy = cv2.findContours(mask_G, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    if len(contours) != 0:
                        for contour in contours:
                            if cv2.contourArea(contour) > 500:
                                x, y, w, h = cv2.boundingRect(contour)
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                            if cv2.contourArea(contour) < 4000:
                                forward_backward_velocity = default_drone_forward_backward
                                yaw_velocity = 0
                            elif cv2.contourArea(contour) >= 4000:
                                detect_G = True
                                print('지정된 사이즈의 Green 감지')
                                log_str += '지정된 사이즈의 Green 감지\n'
                                red_detect_img = cv2.imwrite('green_detect_img.png', frame)
                                forward_backward_velocity = -slow_drone_forward_backward
                                up_down_velocity = -default_drone_up_down

                # Green에 접근했지만, QR을 못 읽었을 때
                if detect_G and not QR_G:
                    # QR을 찾는 중
                    data, bbox, rectifiedImage = qrDecoder.detectAndDecode(frame)
                    if len(data) > 0:
                        print("Decoded Data : {}".format(data))
                        log_str += f'Decoded Data : {data}\n'
                        print(f'result : {calc_func(data)}')
                        log_str += f'result : {calc_func(data)}\n'
                        rectifiedImage = np.uint8(rectifiedImage)
                        QR_G = True


                # Green 탐색 후 Red 탐색 단계
                if detect_G and not detect_R and QR_G:
                    print('Red 탐색 중')
                    log_str += 'Red 탐색 중\n'
                    contours, hierarchy = cv2.findContours(mask_R, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    if len(contours) != 0:
                        for contour in contours:
                            if cv2.contourArea(contour) > 500:
                                x, y, w, h = cv2.boundingRect(contour)
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                            if cv2.contourArea(contour) < 4000:
                                forward_backward_velocity = default_drone_forward_backward
                                yaw_velocity = 0
                            elif cv2.contourArea(contour) >= 4000:
                                detect_R = True
                                print('지정된 사이즈의 Red 감지')
                                log_str += '지정된 사이즈의 Red 감지\n'
                                red_detect_img = cv2.imwrite('red_detect_img.png', frame)
                                forward_backward_velocity = -slow_drone_forward_backward
                                up_down_velocity = -default_drone_up_down

                # Red에 접근했지만, QR을 못 읽었을 때
                if detect_G and detect_R and not QR_R:
                    # QR을 찾는 중
                    data, bbox, rectifiedImage = qrDecoder.detectAndDecode(frame)
                    if len(data) > 0:
                        print("Decoded Data : {}".format(data))
                        log_str += f'Decoded Data : {data}\n'
                        print(f'result : {calc_func(data)}')
                        log_str += f'result : {calc_func(data)}\n'
                        rectifiedImage = np.uint8(rectifiedImage)
                        QR_G = True

                # Green, Red 탐색 후 Blue 탐색 단계
                if detect_G and detect_R and not detect_B and QR_G and QR_B:
                    print('Blue 탐색 중')
                    log_str += 'Blue 탐색 중\n'
                    contours, hierarchy = cv2.findContours(mask_B, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    if len(contours) != 0:
                        for contour in contours:
                            if cv2.contourArea(contour) > 500:
                                x, y, w, h = cv2.boundingRect(contour)
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                            if cv2.contourArea(contour) < 4000:
                                forward_backward_velocity = default_drone_forward_backward
                                yaw_velocity = 0
                            elif cv2.contourArea(contour) >= 4000:
                                detect_B = True
                                print('지정된 사이즈의 Blue 감지')
                                log_str += '지정된 사이즈의 Blue 감지\n'
                                red_detect_img = cv2.imwrite('blue_detect_img.png', frame)
                                forward_backward_velocity = -slow_drone_forward_backward
                                up_down_velocity = -default_drone_up_down

                # Blue에 접근했지만, QR을 못 읽었을 때
                if detect_G and detect_R and detect_B and not QR_B:
                    # QR을 찾는 중
                    data, bbox, rectifiedImage = qrDecoder.detectAndDecode(frame)
                    if len(data) > 0:
                        print("Decoded Data : {}".format(data))
                        log_str += f'Decoded Data : {data}\n'
                        print(f'result : {calc_func(data)}')
                        log_str += f'result : {calc_func(data)}\n'
                        rectifiedImage = np.uint8(rectifiedImage)
                        QR_G = True

                # G, B, R의 QR을 모두 감지 시 강제 종료
                if QR_G and QR_R and QR_B:
                    raise KeyboardInterrupt

        drone.send_rc_control(left_right_velocity, forward_backward_velocity, up_down_velocity, yaw_velocity)

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # quit from script
            break

# 강제 종료에 대한 예외처리
except KeyboardInterrupt:
    print('KeyboardInterrupt 발생. 프로그램 종료합니다.')
    log_str += 'KeyboardInterrupt 발생. 프로그램 종료합니다.\n'
    log_str += ('time: ' + str(time.time() - start_time) + '\n')
    f.write(log_str)
    f.close()
    drone.land()
    cv2.destroyAllWindows()

