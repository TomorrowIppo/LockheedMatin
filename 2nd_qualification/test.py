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

default_drone_up_down = 10
default_drone_right_left = 10
default_drone_forward_backward = 10
default_drone_yaw = 30

lower_blue = np.array([100, 150, 0])
upper_blue = np.array([140, 255, 255])

lower_green = np.array([50, 150, 50])
upper_green = np.array([80, 255, 255])

lower_red = np.array([0, 50, 50])
upper_red = np.array([10, 255, 255])

drone = tello.Tello()
drone.connect()
print(drone.get_battery())
drone.streamon()

drone.takeoff()

start_time = time.time()
hover_time = 0
init_hover_time = True

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
        mask = cv2.inRange(hsv, lower_red, upper_red)  # 110<->150 Hue(색상) 영역을 지정.
        mask1 = cv2.inRange(hsv, lower_green, upper_green)  # 영역 이하는 모두 날림 검정. 그 이상은 모두 흰색 두개로 Mask를 씌움.
        mask2 = cv2.inRange(hsv, lower_blue, upper_blue)

        if init_height:
            print(drone_height)
            if drone_height == 70:
                init_height = False
                print('------ 고도 초기화 종료 ------')

            elif drone_height < 70:
                up_down_velocity = default_drone_up_down
            else:
                up_down_velocity = -default_drone_up_down

        else:
            if not QR_hover_detect:
                print('hover QR 탐색중')
                qrDecoder = cv2.QRCodeDetector()

                # hover QR을 찾는 중
                data, bbox, rectifiedImage = qrDecoder.detectAndDecode(frame)
                if len(data) > 0 and data == 'hover':
                    print("Decoded Data : {}".format(data))
                    rectifiedImage = np.uint8(rectifiedImage)
                    start_hover = True
                    QR_hover_detect = True

            if start_hover:
                if init_hover_time:
                    print('호버링 시작')
                    hover_time = time.time()
                    init_hover_time = False
                interval = time.time() - hover_time
                if 5.0 <= interval and interval <= 5.1:
                    start_hover = False
                    print(f'호버링 끝, interval : {interval}')
                    break

        drone.send_rc_control(left_right_velocity, forward_backward_velocity, up_down_velocity, yaw_velocity)

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # quit from script
            break

except KeyboardInterrupt:
    pass