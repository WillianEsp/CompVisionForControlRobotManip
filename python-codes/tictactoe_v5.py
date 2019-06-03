"""
:File: tictactoe.py
:Description: | Computer Vision for Tic-Tac-Toe
              | Detect board and pieces
              | Defines next play
              | Sends next play through serial communication following a protocol

:Author: Willian Beraldi Esperandio
:Email: willian.esperandio@gmail.com
:Date: 28/03/2019
:Revision: version 1
:License: MIT License
"""


import cv2
import numpy as np
import random
import math
import serial

"""
--> Class created to break nested for
"""

class BigBreak(Exception): pass

"""
--> Class for colored text
"""

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

"""
--> Class containing constants used in the program
"""

class ProgConst:
    ## Used to create relative positions
    computerLetter = 'W'
    playerLetter = 'B'
    numSquares = 3
    serialPortName = "/dev/ttyS0"
    templateBlack = [[ord('B'),ord('-'),ord('B')],
                     [ord('-'),ord('B'),ord('-')],
                     [ord('B'),ord('-'),ord('B')]]
    templateWhite = [[ord('W'),ord('-'),ord('W')],
                     [ord('-'),ord('W'),ord('-')],
                     [ord('W'),ord('-'),ord('W')]]

"""
-->  Find if image has circles and return their positions
-->  Parameters:
-->          - img: RGB image to process 
-->  Return:
-->          - list of positions if found any circle
-->          - None if didn't find any circle
"""

def findCircles(img):
    blurImg = cv2.GaussianBlur(img, (7, 7), 0)
    grayImg = cv2.cvtColor(blurImg,cv2.COLOR_RGB2GRAY)
    #cv2.imshow('Imagem convertida',grayImg)

    ##Max radius of the circle is half the size of each square
    height, width, channel = img.shape
    maxRadius = width//(ProgConst.numSquares*2)
    
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
        showImage('Detected circles', cimg)

    return circles

"""
-->  Get average gray intensity in a circle area around a specific pixel
-->  Parameters:
-->          - img: image to process
-->          - height: height of the pixel
-->          - width: width of the pixel
-->          - radius: radius of the circle area
-->  Return:
-->          - int value containing average gray intensity
"""

def avgGrayIntensity(img, height, width, radius=20):
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
        
"""
-->  Test circles' positions and return their relative position on
-->  the board
-->  Parameters:
-->          - img: image to process
-->          - posCircles: list of circles' positions
-->  Return:
-->          - List of relative positions:
-->              - 'B' for black pieces
-->              - 'W' for white pieces
-->              - '-' for empty spaces
-->          - None if any invalid circle position
"""

def getRelativePos(img, posCircles, printIntensity = True):
    if posCircles is None:
        return None
    grayImg = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    #cv2.imshow('gray',grayImg)
    height, width, channel = img.shape
    spaceSize = height // ProgConst.numSquares

    #Create matrix 3,3, 1 character unicode (True)
    relativePos = np.chararray((ProgConst.numSquares,ProgConst.numSquares),1,True)
    relativePos[:] = '-'

    for pos in posCircles[0,:]:
        height = pos[1]
        width = pos[0]
        try:
            for i in range(ProgConst.numSquares):
                for j in range(ProgConst.numSquares):
                    if i*spaceSize < height < (i+1)*spaceSize and j*spaceSize < width < (j+1)*spaceSize:
                        if relativePos[i][j] == '-':
                            if avgGrayIntensity(grayImg, height, width, 20) >= 127:
                                relativePos[i][j] = 'W'
                                if printIntensity:
                                    print ("Intesity of [",i,",",j,"] = ",avgGrayIntensity(grayImg, height, width, 10), " >= 127 --> White piece")
                            else:
                                relativePos[i][j] = 'B'
                                if printIntensity:
                                    print ("Intesity of [",i,",",j,"] = ",avgGrayIntensity(grayImg, height, width, 10), " < 127 --> Black piece")
                        elif relativePos[i][j] == 'W' or relativePos[i][j] == 'B':
                            return None
                        raise BigBreak
        except:
            pass
    relativePos = np.rot90(relativePos)
    return relativePos

"""
-->  Test if board is full of pieces
-->  Parameters:
-->          - board: board to be verified
-->  Return:
-->          - True if it is full
-->          - False if it isn't full
"""

def isFull(board):
    return ((board[0][0] != '-' and board[0][1] != '-' and board[0][2] != '-') and
            (board[1][0] != '-' and board[1][1] != '-' and board[1][2] != '-') and
            (board[2][0] != '-' and board[2][1] != '-' and board[2][2] != '-'))

"""
-->  Test if desired player won the game
-->  Parameters:
-->          - board: board to be verified
-->          - letter: letter of the player to be verified
-->  Return:
-->          - True if he won the game
-->          - False if the didn't win the game
"""

def isWinner(board, letter):
    return ((board[0][0] == letter and board[0][1] == letter and board[0][2] == letter) or #top row
            (board[1][0] == letter and board[1][1] == letter and board[1][2] == letter) or #middle row
            (board[2][0] == letter and board[2][1] == letter and board[2][2] == letter) or #bottom row
            (board[0][0] == letter and board[1][0] == letter and board[2][0] == letter) or #left column
            (board[0][1] == letter and board[1][1] == letter and board[2][1] == letter) or #middle column
            (board[0][2] == letter and board[1][2] == letter and board[2][2] == letter) or #right column
            (board[0][0] == letter and board[1][1] == letter and board[2][2] == letter) or #diagonal 1
            (board[2][0] == letter and board[1][1] == letter and board[0][2] == letter))   #diagonal 2

"""
-->  Discover next computer move following this rules:
-->          1. Try any winning move
-->          2. Block any opponent winning move
-->          3. Try any corner
-->          4. Try center
-->          5. Try any side
-->  Parameters:
-->          - board: board to be verified
-->  Return:
-->          - Tuple with chosen space
"""
         
def getComputerMove(board):

    #Check if there is any move that wins the game
    for i in range(ProgConst.numSquares):
        for j in range(ProgConst.numSquares):
            copy = board.copy()
            if copy[i][j] == '-':
                copy[i][j] = ProgConst.computerLetter
                if isWinner(copy, ProgConst.computerLetter):
                    print('Move: Winning move - ('+str(i)+","+str(j)+")")
                    return i,j
                
    # Check if the player could win on his next move, and block them.
    for i in range(ProgConst.numSquares):
        for j in range(ProgConst.numSquares):
            copy = board.copy()
            if copy[i][j] == '-':
                copy[i][j] = ProgConst.playerLetter
                if isWinner(copy, ProgConst.playerLetter):
                    print('Move: Blocking move - ('+str(i)+","+str(j)+")")
                    return i,j

    # Try to take one of the corners, if they are free.
    moves = [[0,0],[0,2],[2,0],[2,2]]
    possibleMoves = []
    for move in moves:
        if board[move[0]][move[1]] == '-':
            possibleMoves.append(move)
    if possibleMoves != []:
        move = random.choice(possibleMoves)
        print('Move: Corner move - ('+str(move[0])+","+str(move[1])+")")
        return move
        

    # Try to take the center, if it is free.
    if board[1,1] == '':
        print('Move: Center move - (1,1)')
        return 1,1

    # Move on one of the sides.
    moves = [[0,1],[1,0],[1,2],[2,1]]
    possibleMoves = []
    for move in moves:
        if board[move[0]][move[1]] == '-':
            possibleMoves.append(move)
    if possibleMoves != []:
        move = random.choice(possibleMoves)
        print('Move: Side move - ('+str(move[0])+","+str(move[1])+")")
        return move

"""
-->  Computes cosine value from three points
-->  Parameters:
-->          - p0: end of x-axis point
-->          - p1: center point
-->          - p2: end of y-axis point
-->  Return:
-->          - Float value of cosine
"""

def angleCos(p0, p1, p2):
    d1, d2 = (p0-p1).astype('float'), (p2-p1).astype('float')
    return abs( np.dot(d1, d2) / np.sqrt( np.dot(d1, d1)*np.dot(d2, d2) ) )

"""
-->  Find squares in a given image and filter them with preset parameters
-->  Parameters:
-->          - img: desired RGB image
-->  Return:
-->          - list of squares (None if fails)
"""

def findSquares(img, maxCountourArea = 4000, maxAspectRatioDiff = 0.1):
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
                if (len(cnt) == 4 and cv2.contourArea(cnt) > maxCountourArea and cv2.isContourConvex(cnt) and
                    aspectRatio < (1+maxAspectRatioDiff) and aspectRatio > (1-maxAspectRatioDiff)):
                    cnt = cnt.reshape(-1, 2)
                    max_cos = np.max([angleCos( cnt[i], cnt[(i+1) % 4], cnt[(i+2) % 4] ) for i in range(4)])
                    if max_cos < 0.1:
                        squares.append(cnt)
    if len(squares) == 0:
        return None
    else:
        return squares

"""
-->  Find the position of the board in the image and return position and sizes
-->  Parameters:
-->          - img: image to be processed
-->  Return:
-->          - x: starting position on the x-axis
-->          - y: starting position on the y-axis
-->          - height: x-axis size of the board
-->          - width: y-axis size of the board
-->          - If not successful, return -1
"""

def configureBoardPosition(img, areaSize = 1000):
    print ("Trying to find the board with size < " + str(areaSize) + "... ", end="", flush=True)
    squares = findSquares(img,areaSize)
    if squares is not None:
        contourImg = img.copy()
        for square in squares:
            #cv2.drawContours(contourImg, [square], 0, (0, 255, 0), 2 )
            x,y,w,h = cv2.boundingRect(square)
            posCircles = findCircles(img[y:y+h,x:x+w])
            board = getRelativePos(img[y:y+h,x:x+w], posCircles, False)
            
            if comparePresetBoard(board): 
                ## --- Preset matched
                cv2.drawContours(contourImg, [square], 0, (0, 0, 255), 2 )
                showImage('Board detection',contourImg)
                return x,y,h,w
    
    ## --- Board not found, trying again or aborting
    print("FAIL")
    if (img.size > areaSize*1.5):
        ## --- Trying with larger squares
        return configureBoardPosition(img, areaSize*1.5)
    else:
        ## --- Last try, trying with maximum areaSize (size of the image)
        if(img.size < areaSize*1.5):
            return configureBoardPosition(img,img.size)
        ## --- Max size reached (areaSize = image size), return not found
        else:
            return -1,-1,-1,-1

"""
-->  Test if board detected have all the positions correct
-->  Parameters:
-->          - board: board to be verified
-->  Return:
-->          - True if it is equal to the mix of white and black template
-->          - False if it isn't
"""

def comparePresetBoard(board):
    if board is None:
        return False
    for i in range(ProgConst.numSquares):
        for j in range(ProgConst.numSquares):
            if board[i][j] != ProgConst.templateBlack[i][j] && board[i][j] != ProgConst.templateWhite[i][j]:
                return False
    return True
    
"""
-->  Expand a single board move to all robot moves (Tic-tac-toe only)
-->  Parameters:
-->          - move: board move
-->          - newPiecePos: the position of the new piece array
-->  Return:
-->          - list of expanded movements
"""

def expandMovements(move, newPiecePos):
    expandedMoves = [('n',0,newPiecePos),('p',move[0],move[1])]
    newPiecePos += 1
    return expandedMoves,newPiecePos
    
"""
-->  Convert relative position move to list of commands to send to the robot
-->  Parameters:
-->          - allMoves: list of moves
-->          - commandList: string of commands if exists
-->  Return:
-->          - String of List of commands following the protocol #Sxy$
"""

def convertCommandListToString(allMoves,commandList=None):
    newCommandList = ""
    for move in allMoves:
        newCommandList += "#" + move[0] + str(move[1]) + str(move[2])
    newCommandList += "$"
    if commandList is None:
        return newCommandList
    else:
        return commandList[0:len(commandList)-1]+newCommandList
        
"""
-->  Send data through serial communication
-->  Parameters:
-->          - data: string of desired data
-->  Return:
-->          - None
"""

def sendCommandList(serialPort, data):
    if(serialPort.isOpen()):
        serialPort.write(data)
        return True
    else:
        return False  

"""
-->  Print a better square board with rows and columns numbers
-->  Parameters:
-->          - board: numpy matrix array
-->  Return:
-->          - None
"""

def printBoard(board):
    size = board.shape[0]
    print("\n"+"-"*size+" Printing board ("+str(size)+","+str(size)+") "+"-"*size+"\n")
    for i in range(size):
        if i == 0:
            for j in range(size):
                if j == 0:
                    print("  |  0  |",end="",flush=True)
                else:
                    print("  "+str(j)+"  |",end="",flush=True)
                    if j == size-1:
                        print("")
                        print("  -"+"-"*6*size)
        print(str(i)+" | "+np.array2string(board[i],separator=" | ")[1:-1]+" |")
        print("  -"+"-"*6*size)
    print("")

"""
-->  Complementary version of cv2.imshow to add commands cv2.namedWindow and cv.resizeWindow
-->  to standardize image windows
-->  Parameters:
-->          - windowName: name of the window
-->          - img: image to be displayed
-->  Return:
-->          - None
"""

def showImage(windowName, img):
    cv2.namedWindow(windowName, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_NORMAL)
    cv2.resizeWindow(windowName,640,360)
    cv2.imshow(windowName, img)

"""
-->  Display an image with two diagonal lines from each corner of the image and crossing in the middle
-->  Parameters:
-->          - img: image to be displayed
-->  Return:
-->          - None
"""

def drawCenterLine(windowName, img):
    centerImg = img.copy()
    x,y,c = centerImg.shape
    cv2.line(centerImg,(0,0),(y,x),(255,0,0),2)
    cv2.line(centerImg,(y,0),(0,x),(255,0,0),2)
    showImage(windowName,centerImg)

"""
-->   Main Code
"""

def main():
    cam = cv2.VideoCapture(0)

    # ---- Flags
    computerTurn = False
    centerLines = False
    boardConfigurated = False
    serialConfigurated = False
    executionFlag = False
    errorFlag = False
    
    
    # ---- New pieces list position
    newPiecePos = 0
    
    # ---- Position of the board
    xPos = yPos = eightBoard = widthBoard = -1
    
    ## --- Configuration of the serial port
    serialCounter = 1
    while not serialConfigurated:
        try:
            print("(Attempt " + str(serialCounter) + ") Trying to initialize serial port: " + ProgConst.serialPortName + " ... ", end="", flush = True)
            serialPort = serial.Serial(ProgConst.serialPortName,9600)
            if(serialPort.is_open):
                print(bcolors.OKGREEN + "DONE" + bcolors.ENDC)
                serialConfigurated = True
                executionFlag = True
        except (serial.SerialException, serial.SerialTimeoutException) as error:
            print(bcolors.FAIL +"FAIL - "+error.__str__()+ bcolors.ENDC)
            if serialCounter < 4:
                serialCounter += 1
            else:
                print(bcolors.FAIL + "ERROR: Unable to open serial port!" + bcolors.ENDC)
                errorFlag = True
                break

    ## --- Execution of the computer vision     
    while executionFlag:
        ret_val, img = cam.read(1)
        showImage('Live Feed',img)

        ## --- Configuration of the board size
        if not boardConfigurated:
            print(bcolors.WARNING+"\nSetup the board and press any key to start configuration"+bcolors.ENDC)
            while cv2.waitKey(1) == -1:
                ret_val, img = cam.read(1)
                showImage('Live Feed',img)
            print("\nInitializing board configuration... ")
            xPos, yPos, heightBoard, widthBoard = configureBoardPosition(img)
            if (xPos != -1 and yPos != -1 and heightBoard != -1 and widthBoard != -1):
                print(bcolors.OKGREEN + "DONE" + bcolors.ENDC)
                boardConfigurated = True
            else:
                print(bcolors.FAIL + "FAIL" + bcolors.ENDC)
                print(bcolors.FAIL + "ERROR: Unable to find the board" + bcolors.ENDC)
                executionFlag = False
                errorFlag = True
            print("\n"+bcolors.WARNING+"Clear the board and press any key!"+bcolors.ENDC)
            while cv2.waitKey(1) == -1:
                ret_val, img = cam.read(1)
                showImage('Live Feed',img)
            print("\n--------------------------------------------")
            print("Game started! Place a piece or press <ENTER>")
            print("--------------------------------------------")
        
        ## --- Execution of the main part of the code
        elif computerTurn and boardConfigurated:
            print("\n--------------------")
            print("---- ROBOT TURN ----")
            print("--------------------")
            boardImg = img[yPos:yPos+heightBoard,xPos:xPos+widthBoard]
            
            posCircles = findCircles(boardImg)
            board = getRelativePos(boardImg, posCircles, False)

            if board is None:
                board = np.chararray((3,3),1,True)
                board[:] = '-'
            
            printBoard(board)
            
            if isWinner(board,ProgConst.computerLetter):
                print ("---------------------------------")
                print ("---- THE ROBOT IS THE WINNER ----")
                print ("---------------------------------")
                print ("\nPlease, reset pieces and press <ENTER> to restart the game")
                newPiecePos = 0
                while cv2.waitKey(1) != 13:
                    pass
            
            elif isWinner(board,ProgConst.playerLetter):
                print ("----------------------------------")
                print ("---- THE PLAYER IS THE WINNER ----")
                print ("----------------------------------")
                print ("\nPlease, reset pieces and press <ENTER> to restart the game")
                newPiecePos = 0
                while cv2.waitKey(1) != 13:
                    pass
            
            else:
                move = getComputerMove(board)

                ## Expand, convert and send commands to the robot
                allMoves,newPiecePos = expandMovements(move, newPiecePos)
                commandList = convertCommandListToString(allMoves)
                print("Command sent to Robot: "+commandList)
                
                ##NEED TO TEST IT
                ##if(!sendCommandList(commandList))
                ##    print("COMMUNICATION ERROR");
                ##END OF NEED TO TEST IT
            
            computerTurn = False
        
        ## --- Keyboard inputs        
        else:
            key = cv2.waitKey(1)
            if key == 27: # esc to quit
                executionFlag = False 
                
            elif key == 13: # enter to computer turn
                computerTurn = True 
                
            elif key == 32: # space to configure board
                boardConfigurated = False 
                xPos = yPos = heightBoard = widthBoard = -1
                
            elif key == 8: # backspace to centerLines
                if centerLines == False:
                    centerLines = True
                else:
                    centerLines = False
                    cv2.destroyWindow('Centered Image')             

        ## --- Create a window with image and center lines
        if centerLines == True:
            drawCenterLine('Centered Image',img)
    
    if(errorFlag):
        print(bcolors.WARNING + "Program finishing by error\n" + bcolors.ENDC)
    else:
        print(bcolors.OKBLUE + "Program finishing by keyboard input\n" + bcolors.ENDC)
        
    ##END OF PROGRAM EXECUTION
    serialPort.close()
    cv2.destroyAllWindows()
    cam.release()
        
        
if __name__ == '__main__':
    main()
