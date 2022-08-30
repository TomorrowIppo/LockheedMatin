from djitellopy import tello
import numpy as np
import time
import cv2

start_hover = True
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

#drone.takeoff()

start_time = time.time()
hover_time = 0
init_hover_time = True

try:
    while(True):
        # drone.send_rc_control에 전달할 변수
        left_right_velocity = 0
        forward_backward_velocity = 0
        up_down_velocity = 0
        yaw_velocity = 0
        drone_height = drone.get_height()

        if init_height:
            if drone_height == 70:
                init_height = False

            elif drone_height < 70:
                up_down_velocity = default_drone_up_down
            else:
                up_down_velocity = -default_drone_up_down

        else:
            if start_hover:
                if init_hover_time:
                    hover_time = time.time()
                interval = time.time() - hover_time
                if 5.0 <= interval and interval <= 5.1:
                    start_hover = False

        drone.send_rc_control(left_right_velocity, forward_backward_velocity, up_down_velocity, yaw_velocity)

except KeyboardInterrupt:
    pass

