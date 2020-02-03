from cascade_detection import Detection
from controller import Controller
import cv2
from motor import CalibratedMotor, Motor
from SonarI2C import SonarI2C
import pigpio
import time
from LineTracking import LineTracking

drive_motor = Motor(Motor._bp.PORT_B)
steer_motor = CalibratedMotor(Motor._bp.PORT_D, calpow=20)

def get_noise(pre_dest, dest):
    delta = dest - pre_dest
    if(abs(delta) > 10 and pre_dest > dest):
        return pre_dest
    else: 
        return dest

def drive_steer(pos_new):
    pos = steer_motor.position_from_factor(pos_new)
    steer_motor.change_position(pos)

def drive_power(power_new):
    drive_motor.change_power(power_new)

def stop_all():
    drive_motor.stop()
    steer_motor.stop()

def main():
    cap = cv2.VideoCapture(0)
    det = Detection()
    lt = LineTracking()
    controller = Controller()

    steer_motor.calibrate()

    state = 0
    pi = pigpio.pi()

    if not pi.connected:
        exit(0)
    try:
        octosonar = SonarI2C(pi, int_gpio=25)
        result_list = []
        j = 0
        while True:
            ret, image = cap.read()
            for i in range(2):
                sonar_result = octosonar.read_cm(i)
                time.sleep(0.001)
                if sonar_result is False:
                    result_list.append("Timed out")
                else:
                    result_list.append(round(sonar_result, 1))
                
            if(j == 0):
                dist_front = 50
                dist_side = 50
                j += 1
            elif(j == 1):
                dist_front = result_list[1]
                dist_side = result_list[0]
                j += 1
            else:
                dist_front = get_noise(dist_front, result_list[1])
                dist_side = get_noise(dist_side, result_list[0])
            
            result_list = []
            width = 640
            height = 480

            if(state == 0):
                if(dist_front > 40):
                    print("Following line! Entfernung vorne: {}".format(dist_front))
                    ############TODO: adding line following##########
                    drive_power(-30)
                    #drive_steer(0)
                    val = lt.track_line(image, False)
                    pid = controller.pid(val)
                    #print(pid)
                    drive_steer(pid/100)
                else:
                    drive_power(0)
                    state = 1
            elif(state == 1):
                print("Object in front!")
                det = Detection()
                (x, y, w, h), image = det.detect_palette(image)
                x=-1
                if(x == -1):
                    #Choose value that's on the right side -> when nothing is detected drive around the right side
                    x = 1000
                if(x < int(width / 2)):
                    print("Pallet more on the right side -> drive around the left")
                    state = 2
                else:
                    print("Pallet more on the left side -> drive around the right")
                    state = 3
            elif(state == 2):
                print("Entfernung vorne: {}".format(dist_front))
                print("Drive around left!")
                if(dist_front > 80):
                    print("Right sensor past the pallet!")
                    ############TODO: Value tuning!##################
                    drive_steer(-0.8)
                    drive_power(-30)
                    time.sleep(1)
                    drive_power(0)
                    state = 5
                else:
                    drive_steer(-0.8)
                    drive_power(-30)
            elif(state == 3):
                print("Drive around right!")
                if(dist_front > 80):
                    print("Left sensor past the pallet!")
                    ############TODO: Value tuning!##################
                    #drive_steer(0.8)
                    #drive_power(-30)
                    #time.sleep(1)
                    drive_power(0)
                    state = 5
                else:
                    drive_steer(0.8)
                    drive_power(-30)
            elif(state == 4):
                print("Trying to return on line!")
                if(lt.track_line(image, True) == -1):
                    drive_steer(1)
                    drive_power(-30)
                else:
                    drive_power(0)
            elif(state == 5):
                print("Trying to return on line!")
                ############TODO: General testing!##################
                val = lt.track_line(image, True)
                print(val)
                if(val == -1):
                    drive_steer(-1)
                    drive_power(-30)
                else:
                    drive_steer(0.8)
                    time.sleep(1.2)
                    drive_power(0)
                    state = 0
                


#-----------Show image TODO: Check if waitKey and the Interrupt work together-------------------------------------------------#
            cv2.imshow("frame", image)
            cv2.waitKey(1)
    except KeyboardInterrupt:
        print("\nCTRL-C pressed. Cleaning up and exiting!")
    finally:
        octosonar.cancel()
        cap.release()
        cv2.destroyAllWindows()
        pi.stop()
        stop_all()

main()