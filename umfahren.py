from botlib.bot import Bot
import cv2
from cascade_detection import Detection
from SonarI2C import SonarI2C
import pigpio
import time
from LineTracking import LineTracking
from controller import Controller


def get_noise(pre_dest, dest):
    delta = dest - pre_dest
    if(abs(delta) > 10 and pre_dest > dest):
        return pre_dest
    else: 
        return dest


'''
Problem mit Bot() und Kamera
'''
#bot = Bot()
#print("Calibrating...")
#bot.calibrate()

#controller = Controller()
#lt = LineTracking()

cap = cv2.VideoCapture(0)

'''
Wahrscheinlich Probleme mit den zwei Bot Objekten, evtl. lenken etc. komplett in controller auslagern??
cv2 Bildanzeige gefixed;
evtl. Bildanzeige in umfahren.py integrieren
evtl. LineTracking anpassen oder neu schreiben, um Linie nach umfahren wieder zu finden...
'''

state = 1

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
            time.sleep(0.1)
            width = 640
            height = 480

            if(state == 0):
                #Linefollowingprint("Entfernung vorne: {}; Entfernung Seite: {}".format(dist_front, dist_side))
                if(dist_front > 40):
                    #val = lt.track_line()
                    #controller.controll(val)
                    print("Following line")
                    bot.drive_steer(0)
                    bot.drive_power(0.8)    
                else:
                    print("Palette voraus")
                    bot.drive_forward(0)
                    state = 0
            elif(state == 1):
                #Palette in Sicht
                det = Detection()
                (x, y, w, h),_ = det.detect_palette(image)
                #det.__del__()
                #cv2.destroyAllWindows()
                if(x == -1):
                    (x, y, w, h) = (400, 0, 0, 0)
                if(x < int(width / 2)):
                    print("Palette weiter rechts -> Links umfahren")
                    #controller.drive_forward(-30)
                    state = 1
                else:
                    print("Palette weiter links -> Rechts umfahren")
                    state = 1
            elif(state == 2):
                bot.drive_steer(-0.8)
                if(dist < 40):
                    bot.drive_power(-30)
                else:
                    bot.drive_power(0)
                    print("Rechter Sensor an Palette vorbei")
            elif(state == 3):
                print(dist_front)
                if(dist_front < 80):
                    bot.drive_steer(0.8)
                    bot.drive_power(-30)
                else:
                    bot.drive_power(-30)
                    time.sleep(0.5)
                    bot.drive_power(0)
                    #bot.stop_all()
                    print("Linker Sensor an Palette vorbei")
                    state = 4
            elif(state == 4):
                if(lt.track_line(image) == -1):
                    bot.drive_steer(-0.8)
                    bot.drive_power(-30)
                else:
                    bot.drive_power(0)

            #cv2.imshow("Feed", image)
except KeyboardInterrupt:
    print("\nCTRL-C pressed. Cleaning up and exiting.")
finally:
    cap.release()
    cv2.destroyAllWindows()
    octosonar.cancel()
    pi.stop()
    bot.stop_all()