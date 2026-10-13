// ============================================================
// AI 3-ROAD TRAFFIC SYSTEM
// DENSITY + ACCIDENT LOCK + MANUAL RED/YELLOW/GREEN TRANSITIONS
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
// MANUAL CONTROL MODE
// ============================================================
// When true, Arduino ignores automatic density sequencing.
// Only MANUAL,<ROAD>,<SIGNAL> commands can change lights.
bool manualMode = false;

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
  // --------------------------------------------------------
  // AUTO transition: RED -> YELLOW -> GREEN
  // Same behavior for ROAD A, ROAD B and ROAD C.
  // --------------------------------------------------------

  allRed();
  delay(200);

  Serial.print("AUTO TRANSITION: ROAD ");
  Serial.print(road);
  Serial.println(" RED -> YELLOW");

  // Selected road: RED -> YELLOW.
  if (road == 'A') {
    digitalWrite(A_RED, LOW);
    digitalWrite(A_YELLOW, HIGH);
    digitalWrite(A_GREEN, LOW);
  }
  else if (road == 'B') {
    digitalWrite(B_RED, LOW);
    digitalWrite(B_YELLOW, HIGH);
    digitalWrite(B_GREEN, LOW);
  }
  else if (road == 'C') {
    digitalWrite(C_RED, LOW);
    digitalWrite(C_YELLOW, HIGH);
    digitalWrite(C_GREEN, LOW);
  }
  else {
    Serial.println("AUTO INVALID ROAD");
    allRed();
    return;
  }

  // Yellow duration before GREEN.
  delay(YELLOW_TIME);

  // Selected road: YELLOW -> GREEN.
  if (road == 'A') {
    digitalWrite(A_YELLOW, LOW);
    digitalWrite(A_RED, LOW);
    digitalWrite(A_GREEN, HIGH);
  }
  else if (road == 'B') {
    digitalWrite(B_YELLOW, LOW);
    digitalWrite(B_RED, LOW);
    digitalWrite(B_GREEN, HIGH);
  }
  else if (road == 'C') {
    digitalWrite(C_YELLOW, LOW);
    digitalWrite(C_RED, LOW);
    digitalWrite(C_GREEN, HIGH);
  }

  currentRoad = road;
  currentGreenTime = seconds;
  lightState = GREEN_STATE;
  stateStartTime = millis();

  Serial.print("AUTO TRANSITION: ROAD ");
  Serial.print(road);
  Serial.println(" YELLOW -> GREEN");
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

    if (!manualMode) {
      startNextRoad();
    }

    return;
  }

  // ==========================================================
  // IF ALL RED
  // ==========================================================
  // NEVER restart the automatic sequence in MANUAL mode.

  if (!manualMode && lightState == ALL_RED_STATE) {

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

  if (manualMode) {
    Serial.println(
      "MANUAL MODE ACTIVE - WAITING FOR MANUAL COMMAND"
    );
  }
  else {
    Serial.println(
      "WAITING FOR NEW DENSITY COMMAND"
    );
  }
}

// ============================================================
// PROCESS DENSITY
// ============================================================

void processPriority(String command) {

  command.trim();

  // Never allow an old/new AI density command to control
  // the traffic lights while Telegram MANUAL mode is active.
  if (manualMode) {

    Serial.println(
      "DENSITY COMMAND IGNORED: MANUAL MODE ACTIVE"
    );

    return;
  }

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
// MANUAL MODE
// ============================================================

void enterManualMode() {

  manualMode = true;

  // Stop every automatic timer/state immediately.
  currentRoad = 'X';
  currentGreenTime = 0;
  stateStartTime = millis();
  lightState = ALL_RED_STATE;

  // Start MANUAL with every road RED.
  allRed();

  Serial.println();
  Serial.println("================================");
  Serial.println("MANUAL MODE ENABLED");
  Serial.println("ALL ROADS RED");
  Serial.println("AUTOMATIC TIMER STOPPED");
  Serial.println("================================");
}

// ============================================================
// AUTO MODE
// ============================================================

void enterAutoMode() {

  manualMode = false;

  currentRoad = 'X';
  currentGreenTime = 0;
  stateStartTime = millis();
  lightState = ALL_RED_STATE;

  allRed();

  Serial.println();
  Serial.println("================================");
  Serial.println("AUTO MODE ENABLED");
  Serial.println("================================");

  // Automatic control will start only after a new
  // density priority command is received.
}

// ============================================================
// MANUAL SIGNAL
// ============================================================

void setManualSignal(char road, String signal) {

  if (!manualMode) {
    Serial.println("IGNORED: MANUAL MODE IS NOT ACTIVE");
    return;
  }

  signal.trim();
  signal.toUpperCase();

  // Manual Telegram control supports only RED and GREEN.
  // YELLOW is handled automatically by the UNO when changing
  // from one GREEN road to another GREEN road.

  if (signal == "YELLOW") {
    Serial.println("IGNORED: YELLOW IS AUTOMATIC IN MANUAL MODE");
    return;
  }

  // Never allow GREEN on an incident-locked road.
  if (signal == "GREEN" && isLocked(road)) {

    Serial.print("BLOCKED: ROAD ");
    Serial.print(road);
    Serial.println(" IS INCIDENT LOCKED");

    // Keep the incident road RED.
    if (road == 'A') {
      digitalWrite(A_RED, HIGH);
      digitalWrite(A_YELLOW, LOW);
      digitalWrite(A_GREEN, LOW);
    }
    else if (road == 'B') {
      digitalWrite(B_RED, HIGH);
      digitalWrite(B_YELLOW, LOW);
      digitalWrite(B_GREEN, LOW);
    }
    else if (road == 'C') {
      digitalWrite(C_RED, HIGH);
      digitalWrite(C_YELLOW, LOW);
      digitalWrite(C_GREEN, LOW);
    }

    return;
  }

  // ==========================================================
  // RED
  // ==========================================================

  if (signal == "RED") {

    if (road == 'A') {
      digitalWrite(A_RED, HIGH);
      digitalWrite(A_YELLOW, LOW);
      digitalWrite(A_GREEN, LOW);
    }
    else if (road == 'B') {
      digitalWrite(B_RED, HIGH);
      digitalWrite(B_YELLOW, LOW);
      digitalWrite(B_GREEN, LOW);
    }
    else if (road == 'C') {
      digitalWrite(C_RED, HIGH);
      digitalWrite(C_YELLOW, LOW);
      digitalWrite(C_GREEN, LOW);
    }
    else {
      Serial.println("INVALID MANUAL ROAD");
      return;
    }

    // If the manually controlled road was GREEN,
    // stop tracking it as the active GREEN road.
    if (currentRoad == road) {
      currentRoad = 'X';
      currentGreenTime = 0;
      lightState = ALL_RED_STATE;
      stateStartTime = millis();
    }

    Serial.print("MANUAL -> ROAD ");
    Serial.print(road);
    Serial.println(" RED");

    return;
  }

  // ==========================================================
  // GREEN
  // ==========================================================
  // If another road is currently GREEN, automatically:
  // previous GREEN -> YELLOW -> RED -> selected GREEN.
  //
  // This function uses a short blocking transition because
  // Telegram sends a new GREEN command only when the operator
  // requests a road change.

  if (signal == "GREEN") {

    // Same road already GREEN: do nothing.
    if (currentRoad == road &&
        lightState == GREEN_STATE) {

      Serial.print("ROAD ");
      Serial.print(road);
      Serial.println(" IS ALREADY GREEN");

      return;
    }

    // --------------------------------------------------------
    // PHASE 1: Previous GREEN -> YELLOW -> RED
    // --------------------------------------------------------

    if (currentRoad != 'X' &&
        currentRoad != road &&
        lightState == GREEN_STATE) {

      char previousRoad = currentRoad;

      Serial.print("MANUAL TRANSITION: ROAD ");
      Serial.print(previousRoad);
      Serial.println(" GREEN -> YELLOW");

      // Previous GREEN OFF, previous YELLOW ON.
      if (previousRoad == 'A') {
        digitalWrite(A_GREEN, LOW);
        digitalWrite(A_RED, LOW);
        digitalWrite(A_YELLOW, HIGH);
      }
      else if (previousRoad == 'B') {
        digitalWrite(B_GREEN, LOW);
        digitalWrite(B_RED, LOW);
        digitalWrite(B_YELLOW, HIGH);
      }
      else if (previousRoad == 'C') {
        digitalWrite(C_GREEN, LOW);
        digitalWrite(C_RED, LOW);
        digitalWrite(C_YELLOW, HIGH);
      }

      delay(YELLOW_TIME);

      // Previous road RED.
      if (previousRoad == 'A') {
        digitalWrite(A_YELLOW, LOW);
        digitalWrite(A_RED, HIGH);
      }
      else if (previousRoad == 'B') {
        digitalWrite(B_YELLOW, LOW);
        digitalWrite(B_RED, HIGH);
      }
      else if (previousRoad == 'C') {
        digitalWrite(C_YELLOW, LOW);
        digitalWrite(C_RED, HIGH);
      }

      Serial.print("MANUAL TRANSITION: ROAD ");
      Serial.print(previousRoad);
      Serial.println(" YELLOW -> RED");

      delay(200);
    }

    // --------------------------------------------------------
    // PHASE 2: Selected RED -> YELLOW -> GREEN
    // --------------------------------------------------------
    // This makes the yellow lamp visible before the new road
    // receives GREEN.

    // First make sure every non-selected road is RED.
    allRed();

    delay(200);

    Serial.print("MANUAL TRANSITION: ROAD ");
    Serial.print(road);
    Serial.println(" RED -> YELLOW");

    // Selected road RED OFF, YELLOW ON.
    if (road == 'A') {
      digitalWrite(A_RED, LOW);
      digitalWrite(A_YELLOW, HIGH);
      digitalWrite(A_GREEN, LOW);
    }
    else if (road == 'B') {
      digitalWrite(B_RED, LOW);
      digitalWrite(B_YELLOW, HIGH);
      digitalWrite(B_GREEN, LOW);
    }
    else if (road == 'C') {
      digitalWrite(C_RED, LOW);
      digitalWrite(C_YELLOW, HIGH);
      digitalWrite(C_GREEN, LOW);
    }
    else {
      Serial.println("INVALID MANUAL ROAD");
      allRed();
      return;
    }

    // Automatic yellow duration before GREEN.
    delay(YELLOW_TIME);

    // Selected road YELLOW OFF, GREEN ON.
    if (road == 'A') {
      digitalWrite(A_YELLOW, LOW);
      digitalWrite(A_RED, LOW);
      digitalWrite(A_GREEN, HIGH);
    }
    else if (road == 'B') {
      digitalWrite(B_YELLOW, LOW);
      digitalWrite(B_RED, LOW);
      digitalWrite(B_GREEN, HIGH);
    }
    else if (road == 'C') {
      digitalWrite(C_YELLOW, LOW);
      digitalWrite(C_RED, LOW);
      digitalWrite(C_GREEN, HIGH);
    }

    currentRoad = road;
    currentGreenTime = 0;
    stateStartTime = millis();
    lightState = GREEN_STATE;

    Serial.print("MANUAL TRANSITION: ROAD ");
    Serial.print(road);
    Serial.println(" YELLOW -> GREEN");

    return;
  }

  Serial.println("INVALID MANUAL SIGNAL");
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
  // MANUAL MODE
  // ==========================================================

  if (command == "MANUAL_MODE") {

    enterManualMode();
    return;
  }

  // ==========================================================
  // AUTO MODE
  // ==========================================================

  if (command == "AUTO_MODE") {

    enterAutoMode();
    return;
  }

  // ==========================================================
  // ALL RED
  // ==========================================================

  if (command == "ALL_RED") {

    if (manualMode) {
      allRed();
      currentRoad = 'X';
      currentGreenTime = 0;
      lightState = ALL_RED_STATE;

      Serial.println("MANUAL -> ALL ROADS RED");
    }
    else {
      allRed();
      currentRoad = 'X';
      currentGreenTime = 0;
      lightState = ALL_RED_STATE;

      Serial.println("ALL ROADS RED");
    }

    return;
  }

  // ==========================================================
  // MANUAL SIGNAL
  // ==========================================================

  if (command.startsWith("MANUAL,")) {

    // Expected:
    // MANUAL,A,RED
    // MANUAL,A,GREEN

    int firstComma = command.indexOf(',');
    int secondComma = command.indexOf(',', firstComma + 1);

    if (
      firstComma > 0 &&
      secondComma > firstComma &&
      secondComma < command.length() - 1
    ) {

      char road = command.charAt(firstComma + 1);

      String signal =
        command.substring(secondComma + 1);

      setManualSignal(
        road,
        signal
      );
    }
    else {

      Serial.println("INVALID MANUAL COMMAND");
    }

    return;
  }

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
  Serial.println("MANUAL MODE SUPPORTED");

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
  // AUTOMATIC SIGNAL STATE MACHINE
  // ==========================================================
  // IMPORTANT:
  // In MANUAL mode this entire timer/state machine is disabled.
  // This prevents RED -> YELLOW -> GREEN toggling.

  if (!manualMode && lightState == GREEN_STATE) {

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
    !manualMode &&
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

