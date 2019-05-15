"""
Simply display the contents of the webcam with optional mirroring using OpenCV 
via the new Pythonic cv2 interface.  Press <esc> to quit.
"""

import cv2
import numpy as np
import time


def circle(img, radius):
    img_blur = cv2.GaussianBlur(img, (7, 7), 0)
    gray_img = cv2.cvtColor(img_blur,cv2.COLOR_RGB2GRAY)
    #cv2.imshow('Imagem convertida',gray_img)

    circles = cv2.HoughCircles(gray_img,cv2.HOUGH_GRADIENT,1,50,
                                param1=15,param2=40,minRadius=30,maxRadius=radius)

    cimg = img.copy()
    if(circles is not None):
        circles = np.uint16(np.around(circles))
        #print (len(circles[0,:]))
        for i in circles[0,:]:
            # draw the outer circle
            cv2.circle(cimg,(i[0],i[1]),i[2],(0,255,0),2)
            # draw the center of the circle
            cv2.circle(cimg,(i[0],i[1]),2,(0,0,255),3)
        cv2.imshow('Circles found',cimg)

def angle_cos(p0, p1, p2):
    d1, d2 = (p0-p1).astype('float'), (p2-p1).astype('float')
    return abs( np.dot(d1, d2) / np.sqrt( np.dot(d1, d1)*np.dot(d2, d2) ) )

def find_squares(img):
    img = cv2.GaussianBlur(img, (5, 5), 0)
    img = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    squares = []
    for gray in cv2.split(img):
        for thrs in range(0, 255, 26):
            if thrs == 0:
                bin = cv2.Canny(gray, 0, 50, apertureSize=5)
                bin = cv2.dilate(bin, None)
            else:
                _retval, bin = cv2.threshold(gray, thrs, 255, cv2.THRESH_BINARY)
            bin, contours, hierarchy = cv2.findContours(bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if hierarchy is not None:
                for i in range(len(hierarchy[0])-1,-1,-1):
                    if hierarchy[0][i][3] == -1:
                        del contours[i]

            for cnt in contours:
                cnt_len = cv2.arcLength(cnt, True)
                cnt = cv2.approxPolyDP(cnt, 0.02*cnt_len, True)
                x,y,w,h = cv2.boundingRect(cnt)
                aspectRatio = float (w)/h
                if (len(cnt) == 4 and cv2.contourArea(cnt) > 50000 and cv2.isContourConvex(cnt) and
                    aspectRatio < 1.025 and aspectRatio > 0.975):
                    cnt = cnt.reshape(-1, 2)
                    max_cos = np.max([angle_cos( cnt[i], cnt[(i+1) % 4], cnt[(i+2) % 4] ) for i in range(4)])
                    if max_cos < 0.1:
                        squares.append(cnt)
    if len(squares) == 0:
        return None
    else:
        return squares

def cropBoard(img):
    squares = find_squares(img)
    if squares is not None:
        gray_img = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
        smallestArea = 99999999
        boardSquare = None
        contourImg = img.copy()
        for square in squares:
            #cv2.drawContours(contourImg, [square], 0, (0, 255, 0), 2 )
            squareArea = cv2.contourArea(square)
            if squareArea < smallestArea:
                boardSquare = square
                smallestArea = squareArea
        if boardSquare is not None:
            cv2.drawContours(contourImg, [boardSquare], 0, (0, 255, 0), 2 )
            cv2.imshow('Desired Square',contourImg)
            x,y,w,h = cv2.boundingRect(boardSquare)
            return img[y:y+h,x:x+w]
        else:
            return None
    else:
        return None


def main():
    cam = cv2.VideoCapture(1)
    radius = 50
    computerTurn = False
    centerLines = False
    while True:
        ret_val, img = cam.read(1)
        cv2.imshow('Live Feed', img)
        if computerTurn:
            boardImg = cropBoard(img)
            if boardImg is not None:
                cv2.imshow('Cropped Image', boardImg)
                circle(boardImg,radius)
                if cv2.waitKey(1) == 27: 
                    break  # esc to quit
                computerTurn = False
        else:
            if cv2.waitKey(1) == 27: 
                    break  # esc to quit
            if cv2.waitKey(1) == 13:
                computerTurn = True
            if cv2.waitKey(10) == 8:
                if centerLines == False:
                    centerLines = True
                else:
                    centerLines = False
            if centerLines == True:
                centerImg = img.copy()
                x,y,c = centerImg.shape
                cv2.line(centerImg,(0,0),(y,x),(255,0,0),2)
                cv2.line(centerImg,(y,0),(0,x),(255,0,0),2)
                cv2.imshow('Centered Image', centerImg)
            else:
                cv2.destroyWindow('Centered Image')

    ##END OF PROGRAM EXECUTION
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()

