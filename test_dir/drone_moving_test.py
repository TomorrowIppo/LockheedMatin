import numpy as np
from djitellopy import Tello
from time import sleep
import cv2

TOLERANCE_X = 5
TOLERANCE_Y = 5
SLOWDOWN_THRESHOLD_X = 20
SLOWDOWN_THRESHOLD_Y = 20
DRONE_SPEED_X = 20
init_DRONE_SPEED_Y = 10
default_DRONE_SPEED_Y = 20
slow_DRON_SPEED_Y = 7
DRONE_DIR_Y = 1
DRONE_ROTATE_SPEED = 30
SET_POINT_X = 960 / 2
SET_POINT_Y = 720 / 2

DRONE_UP_MODE = True
IS_DRONE_ROTATE = False
init_height = True

drone = Tello()
drone.connect()
print(drone.get_battery())
drone.streamoff()
drone.streamon()

drone.takeoff()

drone_height = 0
while True:
    up_down_velocity = 0
    yaw_velocity = 0
    DRONE_SPEED_Y = 0
    drone_height = drone.get_height()
    print(drone_height)
    if init_height:
        if drone_height == 80:
            init_height = False
            DRONE_UP_MODE = False
            print('고도 80')
        elif drone_height < 80:
            DRONE_SPEED_Y = init_DRONE_SPEED_Y
        else:
            DRONE_SPEED_Y = -init_DRONE_SPEED_Y

        if DRONE_UP_MODE:
            up_down_velocity = DRONE_SPEED_Y
        else:
            up_down_velocity = -DRONE_SPEED_Y
    else:
        DRONE_SPEED_Y = default_DRONE_SPEED_Y

        if drone_height < 40:
            DRONE_UP_MODE = True
            DRONE_SPEED_Y = default_DRONE_SPEED_Y
            yaw_velocity = DRONE_ROTATE_SPEED
        elif drone_height > 80:
            DRONE_UP_MODE = False
            DRONE_SPEED_Y = default_DRONE_SPEED_Y
            yaw_velocity = DRONE_ROTATE_SPEED

        if 40 < drone_height and drone_height < 50:
            DRONE_SPEED_Y = slow_DRON_SPEED_Y

        if 70 < drone_height and drone_height < 80:
            DRONE_SPEED_Y = slow_DRON_SPEED_Y

        if DRONE_UP_MODE:
            up_down_velocity = DRONE_SPEED_Y
        else:
            up_down_velocity = -DRONE_SPEED_Y


    drone.send_rc_control(0, 0, up_down_velocity, yaw_velocity)







