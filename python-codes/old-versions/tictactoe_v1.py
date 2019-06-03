import cv2
import numpy as np
import random

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

    ## Used to find circles
    circleMinRadius = 50
    circleMaxRadius = 100


## ------------------------------------------------------------------
##  Find if image has circles and return their positions
##  Parameters:
##          - img: RGB image to process 
##  Return:
##          - list of positions if found any circle
##          - None if didn't find any circle
## ------------------------------------------------------------------

def findCircles(img):
    img_blur = cv2.GaussianBlur(img, (7, 7), 0)
    gray_img = cv2.cvtColor(img_blur,cv2.COLOR_RGB2GRAY)
    #cv2.imshow('Imagem convertida',gray_img)

    circles = cv2.HoughCircles(gray_img,cv2.HOUGH_GRADIENT, 1, 50,
                                param1=40, param2=15,
                               minRadius=ProgConst.circleMinRadius, maxRadius=ProgConst.circleMaxRadius)

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
    gray_img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    #cv2.imshow('gray',gray_img)
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
                            if gray_img[height][width] == 255:
                                relativePos[i][j] = 'W'
                            else:
                                relativePos[i][j] = 'B'
                        elif relativePos[i][j] == 'W' or relativePos[i][j] == 'B':
                            return None
                        raise BigBreak
        except:
            pass
    return relativePos

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
## ------------------------------------------------------------------
## ------------------------------------------------------------------
## ------------------------------------------------------------------

def main():
    while(True):
        img = cv2.imread('tictactoe2.jpg')
        cv2.imshow("Imagem Original",img)
        posCircles = findCircles(img)
        board = getRelativePos(img, posCircles)
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
        cv2.waitKey(0)
        
        
if __name__ == '__main__':
    main()
