import numpy as np
import cv2

class Detection():
    #def __init__(self):
    #    self.cap = cv2.VideoCapture(0)

    def detect_palette(self, image):
        #ret, image = self.cap.read()
        paletten_cascade = cv2.CascadeClassifier('cascade_palette_front_48_16.xml')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        palette = paletten_cascade.detectMultiScale(gray, 1.4, 3)

        for (x, y, w, h) in palette:
            print("Palette erkannt bei: X: ({:d}/{:d}), Y: ({:d}/{:d}), W: {:d}, H: {:d}".format(x, 640, y, 480, w, h))
            cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 0), 2)
            return ((x, y, w, h), image)
        return((-1, -1, -1, -1), image)

    #def __del__(self):
    #    self.cap.release()

if __name__ == "__main__":
    det = Detection()
    _, image = det.detect_palette()
    det.__del__()
    cv2.destroyAllWindows()

#if __name__ == "__main__":
#    cap = cv2.VideoCapture(0)
#    ret, image = cap.read()
#    det = Detection()
#    (x, y, w, h), image = det.detect_palette(image)
#    cap.release()