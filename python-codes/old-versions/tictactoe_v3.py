import cv2
import numpy as np
import random
import math
import serial

## ------------------------------------------------------------------
## Class created to break nested for
## ------------------------------------------------------------------

class BigBreak(Exception): pass

## ------------------------------------------------------------------
## Class containing constants used in the program
## ------------------------------------------------------------------

class ProgConst:
    ## Used to create relative positions
    computerLetter = 'W'
    playerLetter = 'B'

## ------------------------------------------------------------------
##  Find if image has circles and return their positions
##  Parameters:
##          - img: RGB image to process 
##  Return:
##          - list of positions if found any circle
##          - None if didn't find any circle
## ------------------------------------------------------------------

def findCircles(img):
    blurImg = cv2.GaussianBlur(img, (7, 7), 0)
    grayImg = cv2.cvtColor(blurImg,cv2.COLOR_RGB2GRAY)
    #cv2.imshow('Imagem convertida',grayImg)

    width, height = grayImg.shape[:2]
    maxRadius = width//6
    
    circles = cv2.HoughCircles(grayImg,cv2.HOUGH_GRADIENT, 1, maxRadius,
                                param1=maxRadius//2, param2=maxRadius,
                               minRadius=maxRadius//2, maxRadius=maxRadius)
    cimg = img.copy()
    if(circles is not None):
        circles = np.uint16(np.around(circles))
        for i in circles[0,:]:
            # draw the outer circle
            cv2.circle(cimg,(i[0],i[1]),i[2],(0,255,0),2)
            # draw the center of the circle
            cv2.circle(cimg,(i[0],i[1]),2,(0,0,255),3)
        cv2.imshow('Imagem processada',cimg)

    return circles

## ------------------------------------------------------------------
##  Get average gray intensity in a circle area around a specific pixel
##  Parameters:
##          - img: image to process
##          - height: height of the pixel
##          - width: width of the pixel
##          - radius: radius of the circle area
##  Return:
##          - int value containing average gray intensity
## ------------------------------------------------------------------

def avgGrayIntensity(img, height, width, radius):
    pixelCount = 0
    sumIntensity = 0
    imgX,imgY = img.shape[0:2]
    for x in range(-radius,radius+1):
        if(height + x > 0 and height+x < imgX):
            y = int(math.sqrt(radius*radius - x*x))
            if (width+y < imgY):
                sumIntensity = sumIntensity + img[height+x][width+y]
                pixelCount = pixelCount + 1
            elif (width - y > 0):
                sumIntensity = sumIntensity + img[height+x][width-y]
                pixelCount = pixelCount + 1
    return (sumIntensity // pixelCount)
        
## ------------------------------------------------------------------
##  Test circles' positions and return their relative position on
##  the board
##  Parameters:
##          - img: image to process
##          - posCircles: list of circles' positions
##  Return:
##          - List of relative positions:
##              - 'B' for black pieces
##              - 'W' for white pieces
##              - 'E' for empty spaces
##          - None if any invalid circle position
## ------------------------------------------------------------------

def getRelativePos(img, posCircles):
    if posCircles is None:
        return None
    grayImg = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    #cv2.imshow('gray',grayImg)
    height, width, channel = img.shape
    spaceSize = height // 3

    #Create matrix 3,3, 1 character unicode (True)
    relativePos = np.chararray((3,3),1,True)
    relativePos[:] = '-'

    for pos in posCircles[0,:]:
        height = pos[1]
        width = pos[0]
        try:
            for i in range(3):
                for j in range(3):
                    if i*spaceSize < height < (i+1)*spaceSize and j*spaceSize < width < (j+1)*spaceSize:
                        if relativePos[i][j] == '-':
                            if avgGrayIntensity(grayImg, height, width, 10) >= 127:
                                relativePos[i][j] = 'W'
                                print ("Intesity of [",i,",",j,"] = ",avgGrayIntensity(grayImg, height, width, 10), " >= 127 --> White piece")
                            else:
                                relativePos[i][j] = 'B'
                                print ("Intesity of [",i,",",j,"] = ",avgGrayIntensity(grayImg, height, width, 10), " < 127 --> Black piece")
                        elif relativePos[i][j] == 'W' or relativePos[i][j] == 'B':
                            return None
                        raise BigBreak
        except:
            pass
    relativePos = np.rot90(relativePos)
    return relativePos

## ------------------------------------------------------------------
##  Test if board is full of pieces
##  Parameters:
##          - board: board to be verified
##  Return:
##          - True if it is full
##          - False if it isn't full
## ------------------------------------------------------------------

def isFull(board):
    return ((board[0][0] != '-' and board[0][1] != '-' and board[0][2] != '-') and
            (board[1][0] != '-' and board[1][1] != '-' and board[1][2] != '-') and
            (board[2][0] != '-' and board[2][1] != '-' and board[2][2] != '-'))

## ------------------------------------------------------------------
##  Test if desired player won the game
##  Parameters:
##          - board: board to be verified
##          - letter: letter of the player to be verified
##  Return:
##          - True if he won the game
##          - False if the didn't win the game
## ------------------------------------------------------------------

def isWinner(board, letter):
    return ((board[0][0] == letter and board[0][1] == letter and board[0][2] == letter) or #top row
            (board[1][0] == letter and board[1][1] == letter and board[1][2] == letter) or #middle row
            (board[2][0] == letter and board[2][1] == letter and board[2][2] == letter) or #bottom row
            (board[0][0] == letter and board[1][0] == letter and board[2][0] == letter) or #left column
            (board[0][1] == letter and board[1][1] == letter and board[2][1] == letter) or #middle column
            (board[0][2] == letter and board[1][2] == letter and board[2][2] == letter) or #right column
            (board[0][0] == letter and board[1][1] == letter and board[2][2] == letter) or #diagonal 1
            (board[2][0] == letter and board[1][1] == letter and board[0][2] == letter))   #diagonal 2

## ------------------------------------------------------------------
##  Discover next computer move following this rules:
##          1. Try any winning move
##          2. Block any opponent winning move
##          3. Try any corner
##          4. Try center
##          5. Try any side
##  Parameters:
##          - board: board to be verified
##  Return:
##          - Tuple with chosen space
## ------------------------------------------------------------------
         
def getComputerMove(board):

    #Check if there is any move that wins the game
    for i in range(3):
        for j in range(3):
            copy = board.copy()
            if copy[i][j] == '-':
                copy[i][j] = ProgConst.computerLetter
                if isWinner(copy, ProgConst.computerLetter):
                    print('Winning move')
                    return i,j
                
    # Check if the player could win on his next move, and block them.
    for i in range(3):
        for j in range(3):
            copy = board.copy()
            if copy[i][j] == '-':
                copy[i][j] = ProgConst.playerLetter
                if isWinner(copy, ProgConst.playerLetter):
                    print('Blocking move')
                    return i,j

    # Try to take one of the corners, if they are free.
    moves = [[0,0],[0,2],[2,0],[2,2]]
    possibleMoves = []
    for move in moves:
        if board[move[0]][move[1]] == '-':
            possibleMoves.append(move)
    if possibleMoves != []:
        print('Corner move')
        return random.choice(possibleMoves)
        

    # Try to take the center, if it is free.
    if board[1,1] == '':
        return 1,1

    # Move on one of the sides.
    moves = [[0,1],[1,0],[1,2],[2,1]]
    possibleMoves = []
    for move in moves:
        if board[move[0]][move[1]] == '-':
            possibleMoves.append(move)
    if possibleMoves != []:
        print('Side move')
        return random.choice(possibleMoves)

## ------------------------------------------------------------------
##  Computes cosine value from three points
##  Parameters:
##          - p0: end of x-axis point
##          - p1: center point
##          - p2: end of y-axis point
##  Return:
##          - Float value of cosine
## ------------------------------------------------------------------

def angleCos(p0, p1, p2):
    d1, d2 = (p0-p1).astype('float'), (p2-p1).astype('float')
    return abs( np.dot(d1, d2) / np.sqrt( np.dot(d1, d1)*np.dot(d2, d2) ) )

## ------------------------------------------------------------------
##  Find squares in a given image and filter them with preset parameters
##  Parameters:
##          - img: desired RGB image
##  Return:
##          - list of squares (None if fails)
## ------------------------------------------------------------------

def findSquares(img):
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
                if (len(cnt) == 4 and cv2.contourArea(cnt) > 4000 and cv2.isContourConvex(cnt) and
                    aspectRatio < 1.1 and aspectRatio > 0.9):
                    cnt = cnt.reshape(-1, 2)
                    max_cos = np.max([angleCos( cnt[i], cnt[(i+1) % 4], cnt[(i+2) % 4] ) for i in range(4)])
                    if max_cos < 0.1:
                        squares.append(cnt)
    if len(squares) == 0:
        return None
    else:
        return squares

## ------------------------------------------------------------------
##  Crop image to contain only the board
##  Parameters:
##          - img: desired RGB image
##  Return:
##          - cropped RGB image or None if fails
## ------------------------------------------------------------------

def cropBoard(img):
    squares = findSquares(img)
    if squares is not None:
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
            cv2.drawContours(contourImg, [boardSquare], 0, (0, 0, 255), 2 )
            cv2.imshow('Desired Square',contourImg)
            x,y,w,h = cv2.boundingRect(boardSquare)
            return img[y:y+h,x:x+w]
        else:
            return None
    else:
        return None

## ------------------------------------------------------------------
##  Expand a single board move to all robot moves (Tic-tac-toe only)
##  Parameters:
##          - move: board move
##          - newPiecePos: the position of the new piece array
##  Return:
##          - list of expanded movements
## ------------------------------------------------------------------

def expandMovements(move, newPiecePos):
    expandedMoves = [('n',0,newPiecePos),('p',move[0],move[1])]
    newPiecePos += 1
    return expandedMoves,newPiecePos
    
## ------------------------------------------------------------------
##  Convert relative position move to list of commands to send to the robot
##  Parameters:
##          - allMoves: list of moves
##          - commandList: string of commands if exists
##  Return:
##          - String of List of commands following the protocol #Sxy$
## ------------------------------------------------------------------

def convertCommandListToString(allMoves,commandList=None):
    newCommandList = ""
    for move in allMoves:
        newCommandList += "#" + move[0] + str(move[1]) + str(move[2])
    newCommandList += "$"
    if commandList is None:
        return newCommandList
    else:
        return commandList[0:len(commandList)-1]+newCommandList
        
# ------------------------------------------------------------------
##  Send data through serial communication
##  Parameters:
##          - data: string of desired data
##  Return:
##          - None
## ------------------------------------------------------------------

def sendCommandList(serialPort, data):
    if(serialPort.isOpen()):
        serialPort.write(data)
        return True
    else:
        return False    
## ------------------------------------------------------------------
## ------------------------------------------------------------------
## ------------------------------------------------------------------
## ------------------------------------------------------------------

def main():
    cam = cv2.VideoCapture(0)
    computerTurn = False
    centerLines = False
    
    newPiecePos = 0
    
    serialPort = serial.Serial("/dev/ttyS0",9600)
  
    while True:
        ret_val, img = cam.read(1)
        cv2.imshow('Live Feed', img)

        if computerTurn:
            print("Computer turn")
            boardImg = cropBoard(img)
            if boardImg is not None:
                posCircles = findCircles(boardImg)
                board = getRelativePos(boardImg, posCircles)

                if (board is not None and (isWinner(board,ProgConst.computerLetter) or isWinner(board,ProgConst.playerLetter))):
                    print ("------------------")
                    print ("WE HAVE A WINNER!!")
                    print ("WE HAVE A WINNER!!")
                    print ("WE HAVE A WINNER!!")
                    print ("------------------")
                elif (board is not None and isFull(board)):
                    print ("------------")
                    print ("IT'S A TIE!!")
                    print ("IT'S A TIE!!")
                    print ("IT'S A TIE!!")
                    print ("------------") 
                else:
                    if board is not None:
                        print(board)
                        move = getComputerMove(board)
                        print (move)
                    else:
                        board = np.chararray((3,3),1,True)
                        board[:] = '-'
                        move = getComputerMove(board)
                        print(board)
                        print (move)

                    ## Expand, convert and send commands to the robot
                    ##NEED TO TEST IT
                    allMoves,newPiecePos = expandMovements(move, newPiecePos)
                    commandList = convertCommandListToString(allMoves)
                    print(commandList)
                    ##if(!sendCommandList(commandList))
                    ##    print("COMMUNICATION ERROR");
                    ##END OF NEED TO TEST IT
            computerTurn = False
            
        else:
            if cv2.waitKey(0) == 27: 
                    break  # esc to quit
            if cv2.waitKey(0) == 13:
                computerTurn = True
            if cv2.waitKey(0) == 8:
                if centerLines == False:
                    centerLines = True
                else:
                    centerLines = False
                    cv2.destroyWindow('Centered Image')
            if centerLines == True:
                centerImg = img.copy()
                x,y,c = centerImg.shape
                cv2.line(centerImg,(0,0),(y,x),(255,0,0),2)
                cv2.line(centerImg,(y,0),(0,x),(255,0,0),2)
                cv2.imshow('Centered Image', centerImg)                

    ##END OF PROGRAM EXECUTION
    cv2.destroyAllWindows()
        
        
if __name__ == '__main__':
    main()
