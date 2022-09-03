from djitellopy import tello
import numpy as np
import cv2

drone = tello.Tello()
drone.connect()
print(drone.get_battery())

drone.streamon()
drone.takeoff()

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

try:
    while True:
        left_right_velocity = 0
        forward_backward_velocity = 0
        up_down_velocity = 0
        yaw_velocity = 0

        frame = drone.get_frame_read().frame

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Threshold the HSV image to get only blue colors
        mask_R = cv2.inRange(hsv, lower_red, upper_red)  # 110<->150 Hue(색상) 영역을 지정.
        mask_G = cv2.inRange(hsv, lower_green, upper_green)  # 영역 이하는 모두 날림 검정. 그 이상은 모두 흰색 두개로 Mask를 씌움.
        mask_B = cv2.inRange(hsv, lower_blue, upper_blue)

        contours, hierarchy = cv2.findContours(mask_R, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) != 0:
            for contour in contours:
                if (cv2.contourArea(contour) > 500) and (cv2.contourArea(contour) < 4000):
                    forward_backward_velocity = default_drone_forward_backward
                    yaw_velocity = 0
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                elif cv2.contourArea(contour) >= 4000:
                    forward_backward_velocity = 0
                    detect_G = True
                    print('지정된 사이즈의 Blue 감지')
                    #forward_backward_velocity = (-3) * default_drone_forward_backward

        #drone.send_rc_control(left_right_velocity, forward_backward_velocity, up_down_velocity, yaw_velocity)

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # quit from script
            break
except KeyboardInterrupt:
    pass
    drone.land()