import numpy as np
import cv2
img = cv2.imread('xiaor.jpg',3)
cv2.imshow('image',img)
cv2.waitKey(0)
cv2.destroyAllWindows()