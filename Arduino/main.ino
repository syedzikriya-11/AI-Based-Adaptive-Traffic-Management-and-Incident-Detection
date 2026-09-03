// ============================================================
// AI 3-ROAD TRAFFIC SYSTEM
// DENSITY + ACCIDENT LOCK + YELLOW
// ============================================================

// ROAD A
const int A_RED = 2;
const int A_YELLOW = 3;
const int A_GREEN = 4;

// ROAD B
const int B_RED = 5;
const int B_YELLOW = 6;
const int B_GREEN = 7;

// ROAD C
const int C_RED = 10;
const int C_YELLOW = 11;
const int C_GREEN = 12;


// ============================================================
// INCIDENT LOCKS
// ============================================================

bool incidentA = false;
bool incidentB = false;
bool incidentC = false;


// ============================================================
// DENSITY PRIORITY RECEIVED FROM PYTHON
// ============================================================

char priorityRoads[3] = {'A', 'B', 'C'};
int priorityTimes[3] = {15, 10, 5};


// ============================================================
// CURRENT SEQUENCE
// ============================================================

char activeSequence[3] = {'A', 'B', 'C'};
int activeTimes[3] = {15, 10, 5};

int sequenceLength = 3;
int sequenceIndex = 0;


// ============================================================
// CURRENT ROAD
// ============================================================

char currentRoad = 'X';
char lastRoad = 'X';

int currentGreenTime = 0;


// ============================================================
// STATES
// ============================================================

enum LightState {
  ALL_RED_STATE,
  GREEN_STATE,
  YELLOW_STATE
};

LightState lightState = ALL_RED_STATE;


// ============================================================
// TIMER
// ============================================================

unsigned long stateStartTime = 0;

const unsigned long YELLOW_TIME = 2000;


// ============================================================
// CHECK LOCK
// ============================================================

bool isLocked(char road) {

  if (road == 'A') {
    return incidentA;
  }

  if (road == 'B') {
    return incidentB;
  }

  if (road == 'C') {
    return incidentC;
  }

  return true;
}


// ============================================================
// ALL RED
// ============================================================

void allRed() {

  digitalWrite(A_RED, HIGH);
  digitalWrite(A_YELLOW, LOW);
  digitalWrite(A_GREEN, LOW);

  digitalWrite(B_RED, HIGH);
  digitalWrite(B_YELLOW, LOW);
  digitalWrite(B_GREEN, LOW);

  digitalWrite(C_RED, HIGH);
  digitalWrite(C_YELLOW, LOW);
  digitalWrite(C_GREEN, LOW);
}


// ============================================================
// BUILD ACTIVE SEQUENCE
// ============================================================
//
// 3 available:
// A -> B -> C
//
// B accident:
// A -> C
//
// A accident:
// B -> C
//
// C accident:
// A -> B
//
// Two accidents:
// only remaining road
//
// ============================================================

void buildActiveSequence() {

  sequenceLength = 0;


  // ==========================================================
  // FIRST: USE PYTHON DENSITY PRIORITY
  // ==========================================================

  for (int i = 0; i < 3; i++) {

    char road = priorityRoads[i];
    int seconds = priorityTimes[i];


    // --------------------------------------------------------
    // SKIP INCIDENT ROAD
    // --------------------------------------------------------

    if (isLocked(road)) {
      continue;
    }


    // --------------------------------------------------------
    // PREVENT DUPLICATE ROAD
    // --------------------------------------------------------

    bool alreadyAdded = false;

    for (int j = 0; j < sequenceLength; j++) {

      if (activeSequence[j] == road) {

        alreadyAdded = true;
        break;
      }
    }


    if (alreadyAdded) {
      continue;
    }


    // --------------------------------------------------------
    // ADD ROAD
    // --------------------------------------------------------

    activeSequence[sequenceLength] = road;
    activeTimes[sequenceLength] = seconds;

    sequenceLength++;
  }


  // ==========================================================
  // PRINT ACTIVE SEQUENCE
  // ==========================================================

  Serial.println();
  Serial.println("================================");

  Serial.print("ACTIVE ROADS: ");

  for (int i = 0; i < sequenceLength; i++) {

    Serial.print(activeSequence[i]);

    if (i < sequenceLength - 1) {
      Serial.print(" -> ");
    }
  }

  Serial.println();

  Serial.println("================================");
}


// ============================================================
// START ROAD
// ============================================================

void startRoad(char road, int seconds) {

  if (isLocked(road)) {

    Serial.print("LOCKED ROAD: ");
    Serial.println(road);

    return;
  }


  // ----------------------------------------------------------
  // SAFETY
  // ----------------------------------------------------------

  allRed();

  delay(300);


  // ----------------------------------------------------------
  // ROAD A
  // ----------------------------------------------------------

  if (road == 'A') {

    digitalWrite(A_RED, LOW);
    digitalWrite(A_GREEN, HIGH);
  }


  // ----------------------------------------------------------
  // ROAD B
  // ----------------------------------------------------------

  else if (road == 'B') {

    digitalWrite(B_RED, LOW);
    digitalWrite(B_GREEN, HIGH);
  }


  // ----------------------------------------------------------
  // ROAD C
  // ----------------------------------------------------------

  else if (road == 'C') {

    digitalWrite(C_RED, LOW);
    digitalWrite(C_GREEN, HIGH);
  }


  currentRoad = road;

  currentGreenTime = seconds;

  stateStartTime = millis();

  lightState = GREEN_STATE;


  Serial.println();

  Serial.print("GREEN -> ROAD ");
  Serial.print(road);

  Serial.print(" | ");
  Serial.print(seconds);

  Serial.println(" SEC");
}


// ============================================================
// START NEXT ROAD
// ============================================================

void startNextRoad() {

  // ==========================================================
  // REBUILD SEQUENCE BASED ON CURRENT INCIDENTS
  // ==========================================================

  buildActiveSequence();


  // ==========================================================
  // NO ROAD AVAILABLE
  // ==========================================================

  if (sequenceLength == 0) {

    allRed();

    currentRoad = 'X';

    currentGreenTime = 0;

    lightState = ALL_RED_STATE;

    Serial.println("ALL ROADS LOCKED");

    return;
  }


  // ==========================================================
  // ONLY ONE ROAD AVAILABLE
  // ==========================================================
  //
  // Example:
  //
  // A accident
  // B accident
  //
  // C -> C -> C -> C
  //
  // ==========================================================

  if (sequenceLength == 1) {

    sequenceIndex = 0;

    char road = activeSequence[0];

    int seconds = activeTimes[0];


    Serial.println();
    Serial.print("ONLY AVAILABLE ROAD: ");
    Serial.println(road);

    Serial.println("CONTINUOUS MODE");


    startRoad(
      road,
      seconds
    );

    return;
  }


  // ==========================================================
  // TWO OR THREE ROADS
  // ==========================================================
  //
  // IMPORTANT:
  //
  // We NEVER allow the same road twice.
  //
  // Example:
  //
  // B accident
  //
  // active sequence:
  //
  // A -> C
  //
  // Therefore:
  //
  // A -> C -> A -> C
  //
  // ==========================================================


  // ----------------------------------------------------------
  // FIND NEXT ROAD
  // ----------------------------------------------------------

  char nextRoad = 'X';

  int nextTime = 0;

  int attempts = 0;


  while (attempts < sequenceLength) {

    char candidate =
      activeSequence[sequenceIndex];

    int candidateTime =
      activeTimes[sequenceIndex];


    // Move index for NEXT time

    sequenceIndex++;

    if (sequenceIndex >= sequenceLength) {

      sequenceIndex = 0;
    }


    attempts++;


    // --------------------------------------------------------
    // ROAD LOCKED?
    // --------------------------------------------------------

    if (isLocked(candidate)) {

      continue;
    }


    // --------------------------------------------------------
    // NEVER RUN SAME ROAD TWICE
    // --------------------------------------------------------

    if (
      candidate == lastRoad
      &&
      sequenceLength > 1
    ) {

      continue;
    }


    nextRoad = candidate;
    nextTime = candidateTime;

    break;
  }


  // ==========================================================
  // FALLBACK
  // ==========================================================

  if (nextRoad == 'X') {

    // Since multiple roads should be available,
    // select the first road that is not locked and
    // is different from the previous road.

    for (int i = 0; i < sequenceLength; i++) {

      char candidate =
        activeSequence[i];

      if (
        !isLocked(candidate)
        &&
        candidate != lastRoad
      ) {

        nextRoad = candidate;
        nextTime = activeTimes[i];

        break;
      }
    }
  }


  // ==========================================================
  // START
  // ==========================================================

  if (nextRoad != 'X') {

    startRoad(
      nextRoad,
      nextTime
    );

    return;
  }


  // ==========================================================
  // SAFETY FALLBACK
  // ==========================================================

  allRed();

  currentRoad = 'X';

  lightState = ALL_RED_STATE;
}


// ============================================================
// START YELLOW
// ============================================================

void startYellow() {

  Serial.print("YELLOW -> ROAD ");
  Serial.println(currentRoad);


  // ----------------------------------------------------------
  // TURN GREEN OFF
  // ----------------------------------------------------------

  digitalWrite(A_GREEN, LOW);
  digitalWrite(B_GREEN, LOW);
  digitalWrite(C_GREEN, LOW);


  // ----------------------------------------------------------
  // ALL RED
  // ----------------------------------------------------------

  digitalWrite(A_RED, HIGH);
  digitalWrite(B_RED, HIGH);
  digitalWrite(C_RED, HIGH);


  // ----------------------------------------------------------
  // CURRENT ROAD YELLOW
  // ----------------------------------------------------------

  if (currentRoad == 'A') {

    digitalWrite(A_RED, LOW);
    digitalWrite(A_YELLOW, HIGH);
  }

  else if (currentRoad == 'B') {

    digitalWrite(B_RED, LOW);
    digitalWrite(B_YELLOW, HIGH);
  }

  else if (currentRoad == 'C') {

    digitalWrite(C_RED, LOW);
    digitalWrite(C_YELLOW, HIGH);
  }


  stateStartTime = millis();

  lightState = YELLOW_STATE;
}


// ============================================================
// FINISH YELLOW
// ============================================================

void finishYellow() {

  Serial.print("YELLOW FINISHED -> ROAD ");
  Serial.println(currentRoad);


  // ----------------------------------------------------------
  // REMEMBER LAST ROAD
  // ----------------------------------------------------------

  lastRoad = currentRoad;


  // ----------------------------------------------------------
  // ALL RED
  // ----------------------------------------------------------

  allRed();

  currentRoad = 'X';

  currentGreenTime = 0;

  lightState = ALL_RED_STATE;


  delay(200);


  // ----------------------------------------------------------
  // NEXT ROAD
  // ----------------------------------------------------------

  startNextRoad();
}


// ============================================================
// INCIDENT DETECTED
// ============================================================

void incidentOff(char road) {

  // ----------------------------------------------------------
  // LOCK ROAD
  // ----------------------------------------------------------

  if (road == 'A') {

    incidentA = true;
  }

  else if (road == 'B') {

    incidentB = true;
  }

  else if (road == 'C') {

    incidentC = true;
  }


  Serial.println();
  Serial.println("################################");

  Serial.print("INCIDENT -> ROAD ");
  Serial.println(road);

  Serial.println("ROAD LOCKED RED");

  Serial.println("################################");


  // ==========================================================
  // IF CURRENT ROAD IS THE ACCIDENT ROAD
  // ==========================================================

  if (currentRoad == road) {

    allRed();

    lastRoad = road;

    currentRoad = 'X';

    currentGreenTime = 0;

    lightState = ALL_RED_STATE;


    startNextRoad();

    return;
  }


  // ==========================================================
  // IF ALL RED
  // ==========================================================

  if (lightState == ALL_RED_STATE) {

    startNextRoad();
  }
}


// ============================================================
// INCIDENT CLEARED
// ============================================================

void clearIncident(char road) {

  if (road == 'A') {

    incidentA = false;
  }

  else if (road == 'B') {

    incidentB = false;
  }

  else if (road == 'C') {

    incidentC = false;
  }


  Serial.println();
  Serial.println("################################");

  Serial.print("INCIDENT CLEARED -> ROAD ");
  Serial.println(road);

  Serial.println("################################");


  // ----------------------------------------------------------
  // RESET
  // ----------------------------------------------------------

  allRed();

  currentRoad = 'X';

  currentGreenTime = 0;

  lightState = ALL_RED_STATE;


  Serial.println(
    "WAITING FOR NEW DENSITY COMMAND"
  );
}


// ============================================================
// PROCESS DENSITY
// ============================================================

void processPriority(String command) {

  command.trim();


  if (command.length() < 11) {

    Serial.println(
      "INVALID DENSITY COMMAND"
    );

    return;
  }


  // ==========================================================
  // ROAD 1
  // ==========================================================

  priorityRoads[0] =
    command.charAt(0);

  priorityTimes[0] =
    command.substring(1, 3).toInt();


  // ==========================================================
  // ROAD 2
  // ==========================================================

  priorityRoads[1] =
    command.charAt(4);

  priorityTimes[1] =
    command.substring(5, 7).toInt();


  // ==========================================================
  // ROAD 3
  // ==========================================================

  priorityRoads[2] =
    command.charAt(8);

  priorityTimes[2] =
    command.substring(9, 11).toInt();


  Serial.println();
  Serial.println("================================");

  Serial.print("NEW DENSITY: ");
  Serial.println(command);

  Serial.print("1: ");
  Serial.print(priorityRoads[0]);
  Serial.print(" = ");
  Serial.print(priorityTimes[0]);
  Serial.println(" SEC");

  Serial.print("2: ");
  Serial.print(priorityRoads[1]);
  Serial.print(" = ");
  Serial.print(priorityTimes[1]);
  Serial.println(" SEC");

  Serial.print("3: ");
  Serial.print(priorityRoads[2]);
  Serial.print(" = ");
  Serial.print(priorityTimes[2]);
  Serial.println(" SEC");

  Serial.println("================================");


  // ==========================================================
  // RESTART FROM HIGHEST PRIORITY
  // ==========================================================

  if (lightState == ALL_RED_STATE) {

    sequenceIndex = 0;

    startNextRoad();
  }
}


// ============================================================
// PROCESS SERIAL COMMAND
// ============================================================

void processCommand(String command) {

  command.trim();


  if (command.length() == 0) {

    return;
  }


  Serial.print("RECEIVED: ");
  Serial.println(command);


  // ==========================================================
  // INCIDENT
  // ==========================================================

  if (command.startsWith("OFF,")) {

    char road =
      command.charAt(4);

    incidentOff(road);

    return;
  }


  // ==========================================================
  // CLEAR
  // ==========================================================

  if (command.startsWith("CLEAR,")) {

    char road =
      command.charAt(6);

    clearIncident(road);

    return;
  }


  // ==========================================================
  // DENSITY
  // ==========================================================

  if (command.length() >= 11) {

    processPriority(command);

    return;
  }


  Serial.println(
    "UNKNOWN COMMAND"
  );
}


// ============================================================
// SETUP
// ============================================================

void setup() {

  pinMode(A_RED, OUTPUT);
  pinMode(A_YELLOW, OUTPUT);
  pinMode(A_GREEN, OUTPUT);

  pinMode(B_RED, OUTPUT);
  pinMode(B_YELLOW, OUTPUT);
  pinMode(B_GREEN, OUTPUT);

  pinMode(C_RED, OUTPUT);
  pinMode(C_YELLOW, OUTPUT);
  pinMode(C_GREEN, OUTPUT);


  Serial.begin(9600);


  allRed();


  currentRoad = 'X';
  lastRoad = 'X';

  sequenceIndex = 0;

  lightState = ALL_RED_STATE;


  Serial.println();
  Serial.println("================================");
  Serial.println("AI TRAFFIC SYSTEM READY");
  Serial.println("================================");

  Serial.println();
  Serial.println("NORMAL:");
  Serial.println("A -> B -> C -> A -> B -> C");

  Serial.println();
  Serial.println("A ACCIDENT:");
  Serial.println("B -> C -> B -> C");

  Serial.println();
  Serial.println("B ACCIDENT:");
  Serial.println("A -> C -> A -> C");

  Serial.println();
  Serial.println("C ACCIDENT:");
  Serial.println("A -> B -> A -> B");

  Serial.println();
  Serial.println("TWO ACCIDENTS:");
  Serial.println("ONLY AVAILABLE ROAD CONTINUES");

  Serial.println();
}


// ============================================================
// LOOP
// ============================================================

void loop() {

  // ==========================================================
  // SERIAL
  // ==========================================================

  if (Serial.available() > 0) {

    String command =
      Serial.readStringUntil('\n');

    processCommand(command);
  }


  // ==========================================================
  // GREEN
  // ==========================================================

  if (lightState == GREEN_STATE) {


    // --------------------------------------------------------
    // SAFETY CHECK
    // --------------------------------------------------------

    if (isLocked(currentRoad)) {

      Serial.print(
        "SAFETY STOP -> "
      );

      Serial.println(
        currentRoad
      );


      allRed();

      lastRoad = currentRoad;

      currentRoad = 'X';

      currentGreenTime = 0;

      lightState = ALL_RED_STATE;


      startNextRoad();
    }


    // --------------------------------------------------------
    // GREEN TIMER
    // --------------------------------------------------------

    else if (
      millis() - stateStartTime
      >=
      ((unsigned long)currentGreenTime * 1000UL)
    ) {

      startYellow();
    }
  }


  // ==========================================================
  // YELLOW
  // ==========================================================

  else if (
    lightState == YELLOW_STATE
  ) {

    if (
      millis() - stateStartTime
      >=
      YELLOW_TIME
    ) {

      finishYellow();
    }
  }
}
