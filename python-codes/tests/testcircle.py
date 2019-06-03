import cv2
import numpy as np

img = cv2.imread('imagem.jpg')
##img = cv2.imread('imagem3.jpg',0)
cv2.imshow('imagem',img)
img = cv2.GaussianBlur(img, (7, 5), 0)
cv2.imshow('imagemblur',img)
gray_img = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)


circles = cv2.HoughCircles(gray_img,cv2.HOUGH_GRADIENT,1,30,
                            param1=50,param2=30,minRadius=0,maxRadius=60)

cimg = img
circles = np.uint16(np.around(circles))
for i in circles[0,:]:
    # draw the outer circle
    cv2.circle(cimg,(i[0],i[1]),i[2],(0,255,0),2)
    # draw the center of the circle
    cv2.circle(cimg,(i[0],i[1]),2,(0,0,255),3)

cv2.circle(cimg,(0,0),i[2],(0,0,255),2)
cv2.circle(cimg,(390,390),i[2],(255,0,0),2)

cv2.imshow('detected circles',cimg)
cv2.waitKey(0)
cv2.destroyAllWindows()
