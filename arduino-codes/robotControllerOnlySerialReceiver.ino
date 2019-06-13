/*

:File: robotControllerWithSerialComm.ino
:Description: | Control an anthropomorphic robot with 6 degrees of freedom using PWM,
              | receiving the commands from a RaspberryPi via Serial Communication.
              | All EEPROM data are pre-recorded using another code (programPositionsWithButtons.ino)

:Author: Willian Beraldi Esperandio
:Email: willian.esperandio@gmail.com
:Date: 28/03/2019
:Revision: version 1
:License: MIT License

*/

#include <EEPROM.h>
#include <Servo.h>

// --- Number of rows and columns of the boardgame's board

static const byte MAX_ROWS = 3;
static const byte MAX_COLUMNS = 3;
static const byte MAX_NEW_PIECES = ((MAX_ROWS * MAX_COLUMNS) / 2) + 1;

// --- PWM pins used by the servos

static const byte PIN_SHOULDER = 3;
static const byte PIN_BICEPS = 5;
static const byte PIN_ELBOW = 6;
static const byte PIN_WRIST = 9;
static const byte PIN_WRISTROT = 10;
static const byte PIN_GRIPPER = 11;

// --- Minimum and maximum values for the PWM of each joint
// --- Values taken from https://www.servocity.com/

static const int MIN_PWM_SHOULDER = 553;
static const int MAX_PWM_SHOULDER = 2425;

static const int MIN_PWM_BICEPS = 556;
static const int MAX_PWM_BICEPS = 2420;

static const int MIN_PWM_ELBOW = 553;
static const int MAX_PWM_ELBOW = 2520;

static const int MIN_PWM_WRIST = 553;
static const int MAX_PWM_WRIST = 2425;

static const int MIN_PWM_WRISTROT = 553;
static const int MAX_PWM_WRISTROT = 2520;

static const int MIN_PWM_GRIPPER = 553;
static const int MAX_PWM_GRIPPER = 2425;

// --- Minimum and maximum values for the angle of each joint

static const byte MIN_ANGLE_SHOULDER = 0;
static const byte MAX_ANGLE_SHOULDER = 180;

static const byte MIN_ANGLE_BICEPS = 0;
static const byte MAX_ANGLE_BICEPS = 180;

static const byte MIN_ANGLE_ELBOW = 0;
static const byte MAX_ANGLE_ELBOW = 180;

static const byte MIN_ANGLE_WRIST = 0;
static const byte MAX_ANGLE_WRIST = 180;

static const byte MIN_ANGLE_WRISTROT = 0;
static const byte MAX_ANGLE_WRISTROT = 180;

static const byte MIN_ANGLE_GRIPPER = 0;
static const byte MAX_ANGLE_GRIPPER = 230;

// --- Joints' starting positions

static const byte START_SHOULDER = 92;
static const byte START_BICEPS = 90;
static const byte START_ELBOW = 90;
static const byte START_WRIST = 90;
static const byte START_WRISTROT = 98;
static const byte START_GRIPPER = 160;

// --- Angle value added/sub each time a button is clicked

static const byte ANGLE_PER_CLICK = 2;

// --- Delay between each robot movement in miliseconds
 
static const int DELAY_BETWEEN_MOVES = 2000;

// --- Structure to store each joint angle for each position

struct Joints {
  int shoulder = START_SHOULDER;
  int biceps = START_BICEPS;
  int elbow = START_ELBOW;
  int wrist = START_WRIST;
  int wristRot = START_WRISTROT;
};

struct Gripper{
  int openPos = START_GRIPPER;
  int closedPos = START_GRIPPER;
};

// --- Matrix of positions storing joint angles

Joints approchPositions[MAX_ROWS][MAX_COLUMNS];
Joints finalPositions[MAX_ROWS][MAX_COLUMNS];
Joints newPiecesApprochPosition[MAX_NEW_PIECES];
Joints newPiecesFinalPosition[MAX_NEW_PIECES];
Joints transitionalPosition;
Joints restPosition;
Gripper gripperPositions;

// --- Declaration of servos classes

Servo shoulderServo;
Servo bicepsServo;
Servo elbowServo;
Servo wristServo;
Servo wristRotServo;
Servo gripperServo;

String inputString = "";         // a String to hold incoming data
bool commandReceived = false;  // received all commands
char movement[3] = {' ',' ',' '};

void setup() {  
  // --- Setting up Servos' pins and their min and max PWM values
  shoulderServo.attach(PIN_SHOULDER, MIN_PWM_SHOULDER, MAX_PWM_SHOULDER);
  bicepsServo.attach(PIN_BICEPS, MIN_PWM_BICEPS, MAX_PWM_BICEPS);
  elbowServo.attach(PIN_ELBOW, MIN_PWM_ELBOW, MAX_PWM_ELBOW);
  wristServo.attach(PIN_WRIST, MIN_PWM_WRIST, MAX_PWM_WRIST);
  wristRotServo.attach(PIN_WRISTROT, MIN_PWM_WRISTROT, MAX_PWM_WRISTROT);
  gripperServo.attach(PIN_GRIPPER, MIN_PWM_GRIPPER, MAX_PWM_GRIPPER);
  
  // --- Setting up Serial communication
  Serial.begin(9600);
  
  // --- Getting positions from EEPROM
  getAllEEPROMData();
  //printAllEEPROM();
  openGripper();
  writeServos(restPosition);
  delay(DELAY_BETWEEN_MOVES);
  
  inputString.reserve(30);
}

void loop() {
  
  // --- Wait until eventSerial finish getting the incoming commands
  if(commandReceived){
    //Serial.print(F("\n----- Comando recebido: "));
    //Serial.println(inputString);
    // --- Iterate until there's no more movements to do or some error occur
    while(getMovement() == true){

      //Serial.print(F("\n----- Comando executado: "));
      //Serial.print(movement[0]);
      //Serial.print(movement[1]);
      //Serial.println(movement[2]);
      //Serial.print(F("\n----- Comandos restantes: "));
      //Serial.println(inputString);
      // --- Movement inside the board
      if(movement[0] == 'g' || movement[0] == 'p'){
        movePieceBoard(movement[0],atoi(&movement[1])/10,atoi(&movement[2]));
      }
      
      // --- Movement outside the board
      else if(movement[0] == 'n'){
        getNewPiece(atoi(&movement[1]));
      }
      //Serial.print(F("\n----- Comandos restantes: "));
      //Serial.println(inputString);
    }
    openGripper();
    //Go to the transitional position
    //Serial.println(F("\n----- Posicao de Transicao -----"));
    writeServos(transitionalPosition);
    delay(DELAY_BETWEEN_MOVES);
    writeServos(restPosition);
    delay(DELAY_BETWEEN_MOVES);
  }
}


// --- Function to get/release a piece in the board
// --- Sequence: Transitional -> Approch -> Final -> Action -> Appr
void movePieceBoard(char type, int row, int column){
  if(row > MAX_ROWS-1 || row < 0 || column > MAX_COLUMNS-1 || column < 0){
    //Serial.println(F("Posição da matriz incorreta"));
    return;
  }
  else{
    //Go to the transitional position
    //Serial.println(F("\n----- Posicao de Transicao -----"));
    writeServos(transitionalPosition);
    delay(DELAY_BETWEEN_MOVES);
    
    //Go to the destination's approch position
    //Serial.print(F("\n----- Posicao de Aproximacao ("));
    //Serial.print(row);
    //Serial.print(",");
    //Serial.print(column);
    //Serial.println(") -----");
    writeServos(approchPositions[row][column]);
    delay(DELAY_BETWEEN_MOVES);
    
    //Go to the destination's final position
    //Serial.print(F("\n----- Posicao Final ("));
    //Serial.print(row);
    //Serial.print(",");
    //Serial.print(column);
    //Serial.println(") -----");
    writeServos(finalPositions[row][column]);
    delay(DELAY_BETWEEN_MOVES);
    
    // --- Get the piece (close gripper)
    if(type == 'g'){
      //Serial.println(F("\n----- Fechando gripper -----"));
      closeGripper();
      delay(DELAY_BETWEEN_MOVES);
    }
    
    // --- Release the piece (open gripper)
    else{
      //Serial.println(F("\n----- Abrindo gripper -----"));
      openGripper();
      delay(DELAY_BETWEEN_MOVES);
    }
    
    //Retreat to the destination's approch position
    //Serial.print(F("\n----- Posicao de Aproximacao ("));
    //Serial.print(row);
    //Serial.print(",");
    //Serial.print(column);
    //Serial.println(") -----");
    writeServos(approchPositions[row][column]);
    delay(DELAY_BETWEEN_MOVES); 
  } 
}

void getNewPiece(int index){
  if(index < 0 || index > MAX_NEW_PIECES-1){
    //Serial.println(F("Posição da nova peça incorreta"));
    return;
  }
  else{
    // --- Go to the transitional position
    //Serial.println(F("\n----- Posicao de Transicao -----"));
    writeServos(transitionalPosition);
    delay(DELAY_BETWEEN_MOVES);
    
    // --- Go to the destination's approch position
    //Serial.print(F("\n----- Posicao de Aproximacao ("));
    //Serial.print(index);
    //Serial.println(") -----");
    writeServos(newPiecesApprochPosition[index]);
    delay(DELAY_BETWEEN_MOVES);
    
    // --- Go to the destination's final position
    //Serial.print(F("\n----- Posicao final ("));
    //Serial.print(index);
    //Serial.println(") -----");
    writeServos(newPiecesFinalPosition[index]);
    delay(DELAY_BETWEEN_MOVES);
    
    // --- Get the piece (close gripper)
    //Serial.println(F("\n----- Fechando gripper -----"));
    closeGripper();
    delay(DELAY_BETWEEN_MOVES);
  
    // --- Retreat to the destination's approch position
    //Serial.print(F("\n----- Posicao de Aproximacao ("));
    //Serial.print(index);
    //Serial.println(") -----");
    writeServos(newPiecesApprochPosition[index]);
    delay(DELAY_BETWEEN_MOVES); 
  }
}

// --- Get a movement from the inputString
// --- Movement needs to be as it follow:
// --- Total: 4 or 5 chars
// --- First char : #            -> start of movement command
// --- Second char: 'p', 'g' or 'n'       -> p for place; g for get; n for new
// --- Third char : number (0-9) -> row of the board or first digit of new
// --- Forth char : number (0-9) -> column of the board or second digit of new
// --- Fifth char : $            -> end of movement command
// --- e.g: #p11$ -> only one movement: place at (1,1)
// --- e.g: #g03#p33#n03#p22$ -> four movements: get from (0,3), place at (3,3), new piece from (03), place at (2,2)

bool getMovement(){
  // --- Search for the start of the command (should be at 0)
  int startIndex = inputString.indexOf('#');
  if(startIndex != -1){
    movement[0] = inputString[startIndex+1];
    movement[1] = inputString[startIndex+2];
    movement[2] = inputString[startIndex+3];

    //Serial.print(F("\n-----Movimento detectado: "));
    //Serial.print(movement[0]);
    //Serial.print(movement[1]);
    //Serial.print(movement[2]);
    ////Serial.print(movement[3]);
    // --- Test if all characters from command are correct
    if((movement[0] == 'p' || movement[0] == 'g' || movement[0] == 'n')
          && isDigit(movement[1]) && isDigit(movement[2])){
      inputString = inputString.substring(startIndex+4);
      //Serial.println(F(" ----- VALIDO"));
      return true;
    }
    else{
      //Serial.println(F(" ----- INVALIDO"));
      //Serial.println(F("Pulando comando..."));
      inputString = inputString.substring(startIndex+4);
      return false;
    }
  }
  else if(startIndex == -1){
    inputString="";
    commandReceived = false;
    //Serial.println(F("\nComando incorreto"));
    //Serial.println(F("\nDeletando entrada..."));
    return false;
  }
  else if(inputString.startsWith("$")){
    inputString="";
    commandReceived = false;
    //Serial.println(F("\nFim de comandos"));
    return false;
  }
}


// --- Function to read all EEPROM data and place it into the variables
void getAllEEPROMData(){
  int eeAddress = 0;
  EEPROM.get(eeAddress, approchPositions);
  eeAddress += sizeof(approchPositions);
  
  EEPROM.get(eeAddress,finalPositions);
  eeAddress += sizeof(finalPositions);
  
  EEPROM.get(eeAddress,newPiecesApprochPosition);
  eeAddress += sizeof(newPiecesApprochPosition);
  
  EEPROM.get(eeAddress,newPiecesFinalPosition);
  eeAddress += sizeof(newPiecesFinalPosition);
  
  EEPROM.get(eeAddress,transitionalPosition);
  eeAddress += sizeof(transitionalPosition);
  
  EEPROM.get(eeAddress,restPosition);
  eeAddress += sizeof(restPosition);
  
  EEPROM.get(eeAddress,gripperPositions);
}


// --- Event called when some serial event occur
void serialEvent(){
  while(Serial.available() && !commandReceived){
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a $, set a flag so the main loop can
    // do something about it:
    if (inChar == '$') {
      commandReceived = true;
    }
  }
}

// --- Function to send to the servos their positions
void writeServos(Joints &joints) {
  shoulderServo.write(joints.shoulder);
  bicepsServo.write(joints.biceps);
  elbowServo.write(joints.elbow);
  wristServo.write(joints.wrist);
  wristRotServo.write(joints.wristRot);
}

// --- Function to set the gripper to the open position
void openGripper(){
  gripperServo.write(gripperPositions.openPos);
}

// --- Function to set the gripper to the closed position
void closeGripper(){
  gripperServo.write(gripperPositions.closedPos);
}

void printAllEEPROM(){
  int i,j;
  //Serial.println(F("IMPRIMINDO VALORES DA POSICAO DE APROXIMAÇÃO"));
  for (i = 0; i < MAX_ROWS; i++) {
    for (j = 0; j < MAX_COLUMNS; j++) {   
      // --- Showing the servos' angles
      //Serial.print(F("Imprimindo posição ("));
      //Serial.print(i);
      //Serial.print(F(","));
      //Serial.print(j);
      //Serial.println(F(")"));
      printJointsValues(approchPositions[i][j]);
    }
  }
  
  //Serial.println(F("\n##########################################"));
  //Serial.println(F("IMPRIMINDO VALORES DA POSICAO FINAL"));
  for (i = 0; i < MAX_ROWS; i++) {
    for (j = 0; j < MAX_COLUMNS; j++) {   
      // --- Showing the servos' angles
      //Serial.print(F("\nImprimindo posição ("));
      //Serial.print(i);
      //Serial.print(F(","));
      //Serial.print(j);
      //Serial.println(F(")"));
      printJointsValues(finalPositions[i][j]);
    }
  }

  //Serial.println(F("\n##########################################"));
  //Serial.println(F("IMPRIMINDO VALORES DA POSICAO DE APROXIMAÇÃO DE NOVAS PEÇAS"));
  for (i = 0; i < MAX_NEW_PIECES; i++) {
    printJointsValues(newPiecesApprochPosition[i]);
  }

  //Serial.println(F("\n##########################################"));
  //Serial.println(F("IMPRIMINDO VALORES DA POSICAO RINAL DE NOVAS PEÇAS"));
  for (i = 0; i < MAX_NEW_PIECES; i++) {
    printJointsValues(newPiecesFinalPosition[i]);
  }

  //Serial.println(F("\n##########################################"));
  //Serial.println(F("IMPRIMINDO VALORES DA POSICAO DE TRANSIÇÃO"));
  printJointsValues(transitionalPosition);

  //Serial.println(F("\n##########################################"));
  //Serial.println(F("IMPRIMINDO VALORES DA POSICAO DE DESCANSO"));
  printJointsValues(restPosition);

  //Serial.println(F("\n##########################################"));
  //Serial.println(F("IMPRIMINDO VALORES DA POSICAO DO GRIPPER"));
  printGripperPositions();
}

void printJointsValues(Joints &joints){
  //Serial.println(F("\n----- Imprimindo valores das juntas -----"));
  //Serial.print(F("Shoulder: "));
  //Serial.println(joints.shoulder);
  //Serial.print(F("Biceps: "));
  //Serial.println(joints.biceps);
  //Serial.print(F("Elbow: "));
  //Serial.println(joints.elbow);
  //Serial.print(F("Wrist: "));
  //Serial.println(joints.wrist);
  //Serial.print(F("WristRot: "));
  //Serial.println(joints.wristRot);
}

void printGripperPositions(){
  //Serial.println(F("----- Imprimindo valores das posições da garra -----"));
  //Serial.print(F("Open: "));
  //Serial.println(gripperPositions.openPos);
  //Serial.print(F("Closed: "));
  //Serial.println(gripperPositions.closedPos);
  //Serial.println(F("----------------------------------------------------"));
}
