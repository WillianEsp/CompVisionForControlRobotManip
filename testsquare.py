# Python 2/3 compatibility
import sys
PY3 = sys.version_info[0] == 3

if PY3:
    xrange = range

import numpy as np
import cv2


def angle_cos(p0, p1, p2):
    d1, d2 = (p0-p1).astype('float'), (p2-p1).astype('float')
    return abs( np.dot(d1, d2) / np.sqrt( np.dot(d1, d1)*np.dot(d2, d2) ) )

def find_squares(img):
    img = cv2.GaussianBlur(img, (5, 5), 0)
    squares = []
    for gray in cv2.split(img):
        for thrs in xrange(0, 255, 26):
            if thrs == 0:
                bin = cv2.Canny(gray, 0, 50, apertureSize=5)
                bin = cv2.dilate(bin, None)
            else:
                _retval, bin = cv2.threshold(gray, thrs, 255, cv2.THRESH_BINARY)
            bin, contours, _hierarchy = cv2.findContours(bin, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                cnt_len = cv2.arcLength(cnt, True)
                cnt = cv2.approxPolyDP(cnt, 0.02*cnt_len, True)
                if len(cnt) == 4 and cv2.contourArea(cnt) > 1000 and cv2.isContourConvex(cnt):
                    cnt = cnt.reshape(-1, 2)
                    max_cos = np.max([angle_cos( cnt[i], cnt[(i+1) % 4], cnt[(i+2) % 4] ) for i in xrange(4)])
                    if max_cos < 0.1:
                        squares.append(cnt)
    return squares

if __name__ == '__main__':
    img = cv2.imread('tictactoe4.jpg')
    cv2.namedWindow('Original Image',cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Original Image', 500,500)
    cv2.imshow('Original Image', img)

    cv2.namedWindow('New Image',cv2.WINDOW_NORMAL)
    cv2.resizeWindow('New Image', 500,500)
    cv2.imshow('New Image', img)
    squares = find_squares(img)
    biggestArea = 0
    h,w = img.shape[0:2]
    print (h,w)
    limitArea = (h-150) * (w-150)

    contourImg = img.copy()
    for square in squares:
        if (biggestArea < cv2.contourArea(square) and cv2.contourArea(square) < limitArea):
            bigSquare = square
            biggestArea = cv2.contourArea(square)
    cv2.drawContours(contourImg, [bigSquare], 0, (0, 255, 0), 2 )
    cv2.namedWindow('Desired Square',cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Desired Square', 500,500)
    cv2.imshow('Desired Square',contourImg)
    print (bigSquare)
    
    maximum = 999999
    for corner in bigSquare:
        if (corner[0] + corner[1]) < maximum:
            maximum  = corner[0] + corner[1]
            minimum = maximum
            topLeftCorner = corner

    maximum = 999999
    for corner in bigSquare:
        if minimum < (corner[0] + corner[1]) < maximum:
            maximum  = corner[0] + corner[1]
            topRightCorner = corner
            
    print (topLeftCorner)
    print (topRightCorner)
    teta = np.rad2deg(np.tan((topLeftCorner[1] - topRightCorner[1]) / (topLeftCorner[0] - topRightCorner[0])))
    print (teta)
    print ("---------------------------")
    M = cv2.moments(bigSquare)
    center = (int(M['m10']/M['m00']), int(M['m01']/M['m00']))
    rotMat = cv2.getRotationMatrix2D(center, teta, 1.0)

    rotatedImg = cv2.warpAffine(img, rotMat, img.shape[1::-1], flags=cv2.INTER_LINEAR)

    cv2.namedWindow('Rotation result',cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Rotation result', 500,500)
    cv2.imshow("Rotation result",rotatedImg)

    squares = find_squares(rotatedImg)
    boardImg = rotatedImg.copy()
    biggestArea = 0
    h,w,c = rotatedImg.shape
    limitArea = (h-150) * (w-150)
    for square in squares:
        if (biggestArea < cv2.contourArea(square) and cv2.contourArea(square) < limitArea):
            bigSquare = square
            biggestArea = cv2.contourArea(square)
    cv2.drawContours(boardImg, [bigSquare], 0, (0, 255, 0), 2 )
    cv2.namedWindow('Board Square',cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Board Square', 500,500)
    cv2.imshow('Board Square',boardImg)

    print (bigSquare)
    print('')
    print ("---------------------------")
    print('')

##    mask = np.zeros_like(rotatedImg)
##    cv2.drawContours(mask,[bigSquare],0,255,-1)
##    finalImg = np.zeros_like(rotatedImg)
##    finalImg[mask == 255] = rotatedImg[mask == 255]
##
##    (x,y) = np.where(mask == 255)
##    (topx,topy) = (np.min(x),np.max(y))
##    (bottomx,bottomy) = (np.max(x),np.max(y))
##    finalImg = finalImg[topx:bottomx+1,topy:bottomy+1]
    x,y,w,h = cv2.boundingRect(bigSquare)
    finalImg=rotatedImg[y:y+h,x:x+w]
    cv2.namedWindow('Final Image',cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Final Image', 500,500)
    cv2.imshow('Final Image',finalImg)

    ch = cv2.waitKey(0)
    cv2.destroyAllWindows()
