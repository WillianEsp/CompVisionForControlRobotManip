/*

:File: setupPositionsWithButtons.ino
:Description: | Setup positions of an anthropomorphic robot with 6 degrees of freedom using PWM.
              | Positions are recorded on EEPROM for later use.

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
static const byte MAX_ANGLE_GRIPPER = 180;

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
 
static const int DELAY_BETWEEN_MOVES = 500;

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

// --- Pins used by the control buttons

static const byte PIN_VALUEUP = 2;
static const byte PIN_VALUEDOWN = 4;
static const byte PIN_JOINTUP = 7;
static const byte PIN_JOINTDOWN = 8;

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

void setup() {
  // --- Setting up buttons' pins
  pinMode(PIN_VALUEUP, INPUT);
  pinMode(PIN_VALUEDOWN, INPUT);
  pinMode(PIN_JOINTUP, INPUT);
  pinMode(PIN_JOINTDOWN, INPUT);
  
  // --- Setting up Servos' pins and their min and max PWM values
  shoulderServo.attach(PIN_SHOULDER, MIN_PWM_SHOULDER, MAX_PWM_SHOULDER);
  bicepsServo.attach(PIN_BICEPS, MIN_PWM_BICEPS, MAX_PWM_BICEPS);
  elbowServo.attach(PIN_ELBOW, MIN_PWM_ELBOW, MAX_PWM_ELBOW);
  wristServo.attach(PIN_WRIST, MIN_PWM_WRIST, MAX_PWM_WRIST);
  wristRotServo.attach(PIN_WRISTROT, MIN_PWM_WRISTROT, MAX_PWM_WRISTROT);
  gripperServo.attach(PIN_GRIPPER, MIN_PWM_GRIPPER, MAX_PWM_GRIPPER);
  
  // --- Setting up Serial communication
  Serial.begin(9600);
}

void loop() {
  int i, j;

  openGripper();
  
  // --- Configuring approach and final positions
  Serial.println(F("\n----- Iniciando configuração de posições de aproximação e finais -----"));
  for (i = 0; i < MAX_ROWS; i++) {
    for (j = 0; j < MAX_COLUMNS; j++) {
      Serial.print(F("\n-----> Configurando posição de aproximação ("));
      Serial.print(i);
      Serial.print(F(","));
      Serial.print(j);
      Serial.println(F(")"));
      
      // --- Manually controlling the servos for approch position
      controlJoints(approchPositions[i][j]);
      
      // --- Showing the servos' angles
      printJointsValues(approchPositions[i][j]);

      finalPositions[i][j] = approchPositions[i][j];
      Serial.print(F("\n-----> Configurando posição final ("));
      Serial.print(i);
      Serial.print(F(","));
      Serial.print(j);
      Serial.println(F(")"));
      // --- Manually controlling the servos for final position
      controlJoints(finalPositions[i][j]);

      // --- Showing the servos' angles
      printJointsValues(finalPositions[i][j]);
    }
  }
  Serial.println(F("----- Finalizado configuração de posições de aproximação e finais -----"));
  
  // --- Configuring new pieces approch and final positions
  Serial.println(F("\n----- Iniciando configuração de posições de aproximação e finais de novas peças -----"));
  for (i = 0; i < MAX_NEW_PIECES; i++) {
    Serial.print(F("Configurando posição de aproximação ("));
    Serial.print(i);
    Serial.println(F(")"));

    controlJoints(newPiecesApprochPosition[i]);

    printJointsValues(newPiecesApprochPosition[i]);

    newPiecesFinalPosition[i] = newPiecesApprochPosition[i];
    Serial.print(F("Configurando posição final ("));
    Serial.print(i);
    Serial.println(F(")"));

    controlJoints(newPiecesFinalPosition[i]);

    printJointsValues(newPiecesFinalPosition[i]);
  }
  Serial.println(F("----- Finalizado configuração de posições de aproximação de novas peças -----"));
  
  // --- Configuring transitional position
  Serial.println(F("\n----- Iniciando configuração de posição intermediária -----"));
  controlJoints(transitionalPosition);
  printJointsValues(transitionalPosition);
  Serial.println(F("----- Finalizado configuração de posição intermediária -----"));
  
  // --- Configuring rest position
  Serial.println(F("\n----- Iniciando configuração de posição de descanso -----"));
  controlJoints(restPosition);
  printJointsValues(restPosition);
  Serial.println(F("----- Finalizado configuração de posição de descanso -----"));

  // --- Configuring gripper positions
  Serial.println(F("\n----- Iniciando configuração de posições da garra -----"));
  configureGripper();
  printGripperPositions();
  Serial.println(F("----- Finalizado configuração de posições da garra -----"));
  
  // --- Writing the positional matrix of the servos into the EEPROM
  Serial.println(F("\n----- Iniciando gravação das posições na EEPROM -----"));
  int eeAddress = 0;
  writeAllEEPROM(eeAddress);
  Serial.println(F("----- Finalizado gravação das posições na EEPROM -----"));
  
  // --- Waiting the command to restart configuration
  Serial.println(F("\n----- Configuração terminada. Deseja reiniciar (s,n)? ------"));
  bool restart = false;
  while (!restart)
  {
    while (!Serial.available()) {}
    if (Serial.read() == 's') {
      restart = true;
    }
  }
}

// --- Function to control the servos using the buttons
void controlJoints(Joints &joints) {
  int activeJointIndex = 0; // 0 - Shoulder; 1 - Biceps; 2 - Elbow; 3 - Wrist; 4 - WristRot;
  bool finished = false;

  Serial.println(F("\n----- Alterado para a junta: 0"));
  //Repeat until both value buttons are pressed
  while (!finished)
  {
    // --- Send the positions to the servos
    writeServos(joints);
    
    // --- Both joint buttons are pressed, finish configuration
    if (digitalRead(PIN_JOINTUP) == HIGH && digitalRead(PIN_JOINTDOWN) == HIGH) {
      Serial.println(F("\nTerminando a configuração das juntas"));
      finished = true;
    }
    
    // ---  Joint up button is pressed (move towards the gripper)
    else if (digitalRead(PIN_JOINTUP) == HIGH) {
      if (activeJointIndex != 4) {
        activeJointIndex++;
      }
      Serial.print(F("\n----- Alterado para a junta: "));
      Serial.println(activeJointIndex);
    }
    
    // --- Joint down button is pressed (move towards the base)
    else if (digitalRead(PIN_JOINTDOWN) == HIGH) {
      if (activeJointIndex != 0) {
        activeJointIndex--;
      }
      Serial.print("\n----- Alterado para a junta: ");
      Serial.println(activeJointIndex);
    }
    
    // --- Value up button is pressed (add a fixed value each time it's pressed)
    else if (digitalRead(PIN_VALUEUP) == HIGH) {
      switch (activeJointIndex) {
        case 0:
          joints.shoulder += ANGLE_PER_CLICK;
          if (joints.shoulder > MAX_ANGLE_SHOULDER) {
            joints.shoulder = MAX_ANGLE_SHOULDER;
          }
          Serial.print(F("Alterado para o valor: "));
          Serial.println(joints.shoulder);
          break;
        case 1:
          joints.biceps += ANGLE_PER_CLICK;
          if (joints.biceps > MAX_ANGLE_BICEPS) {
            joints.biceps = MAX_ANGLE_BICEPS;
          }
          Serial.print(F("Alterado para o valor: "));
          Serial.println(joints.biceps);
          break;
        case 2:
          joints.elbow += ANGLE_PER_CLICK;
          if (joints.elbow > MAX_ANGLE_ELBOW) {
            joints.elbow = MAX_ANGLE_ELBOW;
          }
          Serial.print(F("Alterado para o valor: "));
          Serial.println(joints.elbow);
          break;
        case 3:
          joints.wrist += ANGLE_PER_CLICK;
          if (joints.wrist > MAX_ANGLE_WRIST) {
            joints.wrist = MAX_ANGLE_WRIST;
          }
          Serial.print(F("Alterado para o valor: "));
          Serial.println(joints.wrist);
          break;
        case 4:
          joints.wristRot += ANGLE_PER_CLICK;
          if (joints.wristRot > MAX_ANGLE_WRISTROT) {
            joints.wristRot = MAX_ANGLE_WRISTROT;
          }
          Serial.print(F("Alterado para o valor: "));
          Serial.println(joints.wristRot);
          break;
      }
    }
    
    // --- Value down button is pressed (sub a fixed value each time it's pressed)
    else if (digitalRead(PIN_VALUEDOWN) == HIGH) {
      switch (activeJointIndex) {
        case 0:
          joints.shoulder -= ANGLE_PER_CLICK;
          if (joints.shoulder < MIN_ANGLE_SHOULDER) {
            joints.shoulder = MIN_ANGLE_SHOULDER;
          }
          Serial.print(F("Alterado para o valor: "));
          Serial.println(joints.shoulder);
          break;
        case 1:
          joints.biceps -= ANGLE_PER_CLICK;
          if (joints.biceps < MIN_ANGLE_BICEPS) {
            joints.biceps = MIN_ANGLE_BICEPS;
          }
          Serial.print(F("Alterado para o valor: "));
          Serial.println(joints.biceps);
          break;
        case 2:
          joints.elbow -= ANGLE_PER_CLICK;
          if (joints.elbow < MIN_ANGLE_ELBOW) {
            joints.elbow = MIN_ANGLE_ELBOW;
          }
          Serial.print(F("Alterado para o valor: "));
          Serial.println(joints.elbow);
          break;
        case 3:
          joints.wrist -= ANGLE_PER_CLICK;
          if (joints.wrist < MIN_ANGLE_WRIST) {
            joints.wrist = MIN_ANGLE_WRIST;
          }
          Serial.print(F("Alterado para o valor: "));
          Serial.println(joints.wrist);
          break;
        case 4:
          joints.wristRot -= ANGLE_PER_CLICK;
          if (joints.wristRot < MIN_ANGLE_WRISTROT) {
            joints.wristRot = MIN_ANGLE_WRISTROT;
          }
          Serial.print(F("Alterado para o valor: "));
          Serial.println(joints.wristRot);
          break;
      }
    }
    delay(200);
  }
}

// --- Function to configure gripper positions using the buttons
void configureGripper(){
  bool pos = 0; //0 - Open; 1 - Closed
  bool finished = false;
  Serial.println(F("\n----- Iniciando configuração de garra aberta -----"));
  while (!finished)
  {
    // --- Configuring open position
    if(pos == 0){
      
      // --- 
      openGripper();
      // --- Both joint buttons are pressed, finish configuration
      if (digitalRead(PIN_JOINTUP) == HIGH && digitalRead(PIN_JOINTDOWN) == HIGH){
        Serial.println(F("Terminando a configuração da garra"));
        finished = true;
      }
      else if (digitalRead(PIN_JOINTUP) == HIGH){
        Serial.println(F("Alterado para configuração de garra fechada"));
        pos = 1;
      }
      else if (digitalRead(PIN_VALUEUP) == HIGH){
        gripperPositions.openPos += ANGLE_PER_CLICK;
        if(gripperPositions.openPos > MAX_ANGLE_GRIPPER){
          gripperPositions.openPos = MAX_ANGLE_GRIPPER;
        }
        Serial.print(F("Alterado para o valor: "));
        Serial.println(gripperPositions.openPos);
      }
      else if(digitalRead(PIN_VALUEDOWN) == HIGH){
        gripperPositions.openPos -= ANGLE_PER_CLICK;
        if(gripperPositions.openPos > MIN_ANGLE_GRIPPER){
          gripperPositions.openPos = MIN_ANGLE_GRIPPER;
        }
        Serial.print(F("Alterado para o valor: "));
        Serial.println(gripperPositions.openPos);
      }
    }
    
    // --- Configuring closed positions
    else{
      closeGripper();
      if (digitalRead(PIN_JOINTUP) == HIGH && digitalRead(PIN_JOINTDOWN) == HIGH){
        Serial.println(F("Terminando a configuração da garra"));
        finished = true;
      }
      else if (digitalRead(PIN_JOINTDOWN) == HIGH){
        Serial.println(F("Alterado para configuração de garra fechada"));
        pos = 0;
      }
      else if (digitalRead(PIN_VALUEUP) == HIGH){
        gripperPositions.closedPos += ANGLE_PER_CLICK;
        if(gripperPositions.closedPos > 180){
          gripperPositions.closedPos = 180;
        }
        Serial.print(F("Alterado para o valor: "));
        Serial.println(gripperPositions.closedPos);
      }
      else if(digitalRead(PIN_VALUEDOWN) == HIGH){
        gripperPositions.closedPos -= ANGLE_PER_CLICK;
        if(gripperPositions.closedPos > 0){
          gripperPositions.closedPos = 0;
        }
        Serial.print(F("Alterado para o valor: "));
        Serial.println(gripperPositions.closedPos);
      }
    }
    delay(200);
  }
}

// --- Function to set the gripper to the open position
void openGripper(){
  gripperServo.write(gripperPositions.openPos);
}

// --- Function to set the gripper to the closed position
void closeGripper(){
  gripperServo.write(gripperPositions.closedPos);
}

// --- Function to send to the servos their positions
void writeServos(Joints &joints) {
  shoulderServo.write(joints.shoulder);
  bicepsServo.write(joints.biceps);
  elbowServo.write(joints.elbow);
  wristServo.write(joints.wrist);
  wristRotServo.write(joints.wristRot);
}

// --- Function to write all the positions of the servos into the EEPROM
// --- ORDER:
// --- Approch Positions -> Final Positions -> New Pieces Approch -> New Pieces Final ->
// --- -> Transitional Position -> Rest Position -> Gripper Positions
void writeAllEEPROM(int eeAddress){  
  Serial.print(F("Escrevendo matriz de posições de aproximação na EEPROM a partir da posição de memória: "));
  Serial.println(eeAddress);
  Serial.print(F("Tamanho total de bytes da matriz de posições de aproximação: "));
  Serial.println(sizeof(approchPositions));
  EEPROM.put(eeAddress,approchPositions);
  Serial.println(F("Matriz de posições de aproximação escritas na EEPROM corretamente"));
  eeAddress += sizeof(approchPositions);
  
  Serial.print(F("Escrevendo matriz de posições finais na EEPROM a partir da posição de memória: "));
  Serial.println(eeAddress);
  Serial.print(F("Tamanho total de bytes da matriz de posições finais: "));
  Serial.println(sizeof(finalPositions));
  EEPROM.put(eeAddress,finalPositions);
  Serial.println(F("Matriz de posições finais escritas na EEPROM corretamente"));
  eeAddress += sizeof(finalPositions);
  
  Serial.print(F("Escrevendo matriz de posições finais na EEPROM a partir da posição de memória: "));
  Serial.println(eeAddress);
  Serial.print(F("Tamanho total de bytes da matriz de posições finais: "));
  Serial.println(sizeof(newPiecesApprochPosition));
  EEPROM.put(eeAddress,newPiecesApprochPosition);
  Serial.println(F("Matriz de posições finais escritas na EEPROM corretamente"));
  eeAddress += sizeof(newPiecesApprochPosition);
  
  Serial.print(F("Escrevendo matriz de posições finais na EEPROM a partir da posição de memória: "));
  Serial.println(eeAddress);
  Serial.print(F("Tamanho total de bytes da matriz de posições finais: "));
  Serial.println(sizeof(newPiecesFinalPosition));
  EEPROM.put(eeAddress,newPiecesFinalPosition);
  Serial.println(F("Matriz de posições finais escritas na EEPROM corretamente"));
  eeAddress += sizeof(newPiecesFinalPosition);
  
  Serial.print(F("Escrevendo posição de transição na EEPROM a partir da posição de memória: "));
  Serial.println(eeAddress);
  Serial.print(F("Tamanho total de bytes da posição de transição: "));
  Serial.println(sizeof(transitionalPosition));
  EEPROM.put(eeAddress,transitionalPosition);
  Serial.println(F("Posição de transição escrita na EEPROM corretamente"));
  eeAddress += sizeof(transitionalPosition);
  
  Serial.print(F("Escrevendo posição de descanso na EEPROM a partir da posição de memória: "));
  Serial.println(eeAddress);
  Serial.print(F("Tamanho total de bytes da posição de descanso: "));
  Serial.println(sizeof(restPosition));
  EEPROM.put(eeAddress,restPosition);
  Serial.println(F("Posição de descanso escrita na EEPROM corretamente"));
  eeAddress += sizeof(restPosition);
  
  Serial.print(F("Escrevendo posições da garra na EEPROM a partir da posição de memória: "));
  Serial.println(eeAddress);
  Serial.print(F("Tamanho total de bytes das posições da garra: "));
  Serial.println(sizeof(gripperPositions));
  EEPROM.put(eeAddress,gripperPositions);
  Serial.println(F("Posições da garra escritas na EEPROM corretamente"));
}

// --- Function to print the joints values
void printJointsValues(Joints &joints){
  Serial.println(F("\n----- Imprimindo valores das juntas -----"));
  Serial.print(F("Shoulder: "));
  Serial.println(joints.shoulder);
  Serial.print(F("Biceps: "));
  Serial.println(joints.biceps);
  Serial.print(F("Elbow: "));
  Serial.println(joints.elbow);
  Serial.print(F("Wrist: "));
  Serial.println(joints.wrist);
  Serial.print(F("WristRot: "));
  Serial.println(joints.wristRot);
}

// --- Function to print the gripper positions values
void printGripperPositions(){
  Serial.println(F("\n----- Imprimindo valores das posições da garra -----"));
  Serial.print(F("Open: "));
  Serial.println(gripperPositions.openPos);
  Serial.print(F("Closed: "));
  Serial.println(gripperPositions.closedPos);
  Serial.println(F("----------------------------------------------------"));
}
