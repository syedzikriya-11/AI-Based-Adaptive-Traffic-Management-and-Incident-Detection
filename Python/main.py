# ============================================================
# AI 3-ROAD TRAFFIC MANAGEMENT + TELEGRAM ALERTS
#
# FEATURES:
# 1. Vehicle density detection
# 2. AI traffic priority
# 3. Accident detection
# 4. Person fall detection
# 5. Incident road RED LOCK
# 6. Remaining roads continue according to density
# 7. Automatic incident clearing
# 8. Telegram accident/fall notification
# 9. Telegram incident-cleared notification
# 10. One Telegram alert per incident
# ============================================================

import cv2
import time
import serial
import requests

from ultralytics import YOLO


# ============================================================
# TELEGRAM SETTINGS
# ============================================================

# IMPORTANT:
# Put your Telegram BotFather token here.
#
# DO NOT SEND YOUR TOKEN TO ANYONE.

TELEGRAM_BOT_TOKEN = "TOKEN"


# Put the Chat ID you obtained earlier here.

TELEGRAM_CHAT_ID = "chat_id"


# ============================================================
# FILES
# ============================================================

VEHICLE_MODEL = "yolo11n.pt"

ACCIDENT_MODEL = "epoch61.pt"

POSE_MODEL = "yolo11n-pose.pt"


# ============================================================
# ARDUINO
# ============================================================

ARDUINO_PORT = "COM3"

BAUD_RATE = 9600


# ============================================================
# CAMERAS
# ============================================================

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


# ============================================================
# DENSITY SETTINGS
# ============================================================

DENSITY_UPDATE_TIME = 30


# ============================================================
# GREEN TIME
# ============================================================

FIRST_PRIORITY_TIME = 15

SECOND_PRIORITY_TIME = 10

THIRD_PRIORITY_TIME = 5


# ============================================================
# INCIDENT DETECTION
# ============================================================

ACCIDENT_CONFIDENCE = 0.50

PERSON_CONFIDENCE = 0.50


# Number of consecutive frames required
# before an incident is confirmed.

INCIDENT_CONFIRMATIONS = 5


# Number of consecutive clean frames
# before an incident is cleared.

INCIDENT_CLEAR_CONFIRMATIONS = 50


# ============================================================
# TELEGRAM
# ============================================================

# Minimum time between Telegram alerts for safety.
#
# This prevents accidental notification spam.

TELEGRAM_COOLDOWN = 30


# ============================================================
# ROAD INFORMATION
# ============================================================

ROAD_NAMES = [
    "ROAD A",
    "ROAD B",
    "ROAD C"
]

ROAD_LETTERS = [
    "A",
    "B",
    "C"
]


# ============================================================
# LOAD VEHICLE MODEL
# ============================================================

print()
print("==============================================")
print("LOADING VEHICLE MODEL")
print("==============================================")

vehicle_model = YOLO(
    VEHICLE_MODEL
)

print("Vehicle model loaded.")


# ============================================================
# LOAD ACCIDENT MODEL
# ============================================================

print()
print("==============================================")
print("LOADING ACCIDENT MODEL")
print("==============================================")

accident_model = YOLO(
    ACCIDENT_MODEL
)

print("Accident model loaded.")

print(
    "Accident classes:",
    accident_model.names
)


# ============================================================
# LOAD FALL MODEL
# ============================================================

print()
print("==============================================")
print("LOADING FALL DETECTION MODEL")
print("==============================================")

pose_model = YOLO(
    POSE_MODEL
)

print("Fall detection model loaded.")


# ============================================================
# CONNECT ARDUINO
# ============================================================

print()
print("==============================================")
print("CONNECTING TO ARDUINO")
print("==============================================")

try:

    arduino = serial.Serial(
        ARDUINO_PORT,
        BAUD_RATE,
        timeout=1
    )

    # Arduino resets when serial opens.

    time.sleep(2)

    print(
        f"Arduino connected: {ARDUINO_PORT}"
    )

except Exception as e:

    print("Arduino connection failed.")

    print(e)

    raise SystemExit


# ============================================================
# OPEN CAMERAS
# ============================================================

print()
print("==============================================")
print("OPENING CAMERAS")
print("==============================================")


cameras = []


for camera_index in range(3):

    print(
        f"Opening Camera {camera_index} "
        f"-> {ROAD_NAMES[camera_index]}"
    )


    cap = cv2.VideoCapture(
        camera_index,
        cv2.CAP_DSHOW
    )


    cap.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH
    )


    cap.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT
    )


    if cap.isOpened():

        print(
            f"{ROAD_NAMES[camera_index]} camera OK"
        )

    else:

        print(
            f"WARNING: "
            f"{ROAD_NAMES[camera_index]} "
            f"camera not available"
        )


    cameras.append(cap)


# ============================================================
# CREATE WINDOWS
# ============================================================

for road in ROAD_NAMES:

    cv2.namedWindow(
        road,
        cv2.WINDOW_NORMAL
    )

    cv2.resizeWindow(
        road,
        CAMERA_WIDTH,
        CAMERA_HEIGHT
    )


# ============================================================
# INCIDENT STATUS
# ============================================================

incident_active = [
    False,
    False,
    False
]


# ============================================================
# INCIDENT COUNTERS
# ============================================================

incident_confirm_count = [
    0,
    0,
    0
]


incident_clear_count = [
    0,
    0,
    0
]


# ============================================================
# INCIDENT TYPE
# ============================================================

incident_type = [
    None,
    None,
    None
]


# ============================================================
# INCIDENT CONFIDENCE
# ============================================================

incident_confidence = [
    0.0,
    0.0,
    0.0
]


# ============================================================
# TELEGRAM LAST ALERT TIME
# ============================================================

last_telegram_alert = [
    0,
    0,
    0
]


# ============================================================
# TRAFFIC DENSITY
# ============================================================

vehicle_counts = [
    0,
    0,
    0
]


# ============================================================
# COUNT HISTORY
# ============================================================

count_history = [
    [],
    [],
    []
]


# ============================================================
# TIME
# ============================================================

last_density_update = time.time()


# ============================================================
# TELEGRAM FUNCTION
# ============================================================

def send_telegram(message):

    # ----------------------------------------------
    # CHECK TOKEN
    # ----------------------------------------------

    if (
        TELEGRAM_BOT_TOKEN == ""
        or
        TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN"
    ):

        print(
            "WARNING: Telegram bot token not configured."
        )

        return False


    # ----------------------------------------------
    # CHECK CHAT ID
    # ----------------------------------------------

    if (
        TELEGRAM_CHAT_ID == ""
        or
        TELEGRAM_CHAT_ID == "YOUR_CHAT_ID"
    ):

        print(
            "WARNING: Telegram Chat ID not configured."
        )

        return False


    # ----------------------------------------------
    # TELEGRAM API
    # ----------------------------------------------

    url = (
        "https://api.telegram.org/bot"
        +
        TELEGRAM_BOT_TOKEN
        +
        "/sendMessage"
    )


    data = {

        "chat_id": TELEGRAM_CHAT_ID,

        "text": message
    }


    try:

        response = requests.post(
            url,
            data=data,
            timeout=10
        )


        if response.status_code == 200:

            print(
                "📱 TELEGRAM ALERT SENT"
            )

            return True


        else:

            print(
                "Telegram error:"
            )

            print(
                response.text
            )

            return False


    except Exception as e:

        print(
            "Telegram connection error:"
        )

        print(e)

        return False


# ============================================================
# SEND TO ARDUINO
# ============================================================

def send_arduino(command):

    try:

        arduino.write(
            command.encode()
        )

        print(
            f"ARDUINO << {command.strip()}"
        )

    except Exception as e:

        print(
            "Arduino communication error:",
            e
        )


# ============================================================
# ACCIDENT DETECTION
# ============================================================

def detect_accident(frame):

    results = accident_model(
        frame,
        verbose=False
    )

    result = results[0]


    if result.boxes is None:

        return False, 0.0


    detected = False

    highest_confidence = 0.0


    for box in result.boxes:

        confidence = float(
            box.conf[0]
        )


        class_id = int(
            box.cls[0]
        )


        class_name = str(
            accident_model.names[class_id]
        ).lower()


        if (
            "accident" in class_name
            or
            "crash" in class_name
        ):

            if (
                confidence
                >=
                ACCIDENT_CONFIDENCE
            ):

                detected = True


                highest_confidence = max(
                    highest_confidence,
                    confidence
                )


    return (
        detected,
        highest_confidence
    )


# ============================================================
# FALL DETECTION
# ============================================================

def detect_person_fall(frame):

    results = pose_model(
        frame,
        verbose=False
    )

    result = results[0]


    if result.boxes is None:

        return False, 0.0


    if result.keypoints is None:

        return False, 0.0


    fall_detected = False

    highest_confidence = 0.0


    boxes = result.boxes

    keypoints = result.keypoints


    for person_index in range(
        len(boxes)
    ):

        confidence = float(
            boxes[person_index].conf[0]
        )


        if (
            confidence
            <
            PERSON_CONFIDENCE
        ):

            continue


        xyxy = (
            boxes[
                person_index
            ]
            .xyxy[0]
            .cpu()
            .numpy()
        )


        x1, y1, x2, y2 = xyxy


        width = max(
            1,
            x2 - x1
        )


        height = max(
            1,
            y2 - y1
        )


        aspect_ratio = (
            width / height
        )


        if (
            aspect_ratio
            <
            1.20
        ):

            continue


        points = (
            keypoints[
                person_index
            ]
            .xy[0]
            .cpu()
            .numpy()
        )


        if len(points) < 17:

            continue


        # COCO keypoints

        left_shoulder = points[5]

        right_shoulder = points[6]

        left_hip = points[11]

        right_hip = points[12]


        if (
            left_shoulder[0] <= 0
            or
            right_shoulder[0] <= 0
            or
            left_hip[0] <= 0
            or
            right_hip[0] <= 0
        ):

            continue


        shoulder_x = (
            left_shoulder[0]
            +
            right_shoulder[0]
        ) / 2


        shoulder_y = (
            left_shoulder[1]
            +
            right_shoulder[1]
        ) / 2


        hip_x = (
            left_hip[0]
            +
            right_hip[0]
        ) / 2


        hip_y = (
            left_hip[1]
            +
            right_hip[1]
        ) / 2


        dx = hip_x - shoulder_x

        dy = hip_y - shoulder_y


        horizontal_body = (
            abs(dx)
            >
            abs(dy) * 1.20
        )


        if horizontal_body:

            fall_detected = True

            highest_confidence = max(
                highest_confidence,
                confidence
            )


    return (
        fall_detected,
        highest_confidence
    )


# ============================================================
# SEND INCIDENT TELEGRAM ALERT
# ============================================================

def send_incident_alert(
    road_index,
    detected_type,
    confidence
):

    current_time = time.time()


    # ----------------------------------------------
    # COOLDOWN
    # ----------------------------------------------

    if (
        current_time
        -
        last_telegram_alert[road_index]
        <
        TELEGRAM_COOLDOWN
    ):

        print(
            f"Telegram cooldown active "
            f"for {ROAD_NAMES[road_index]}"
        )

        return


    # ----------------------------------------------
    # SAVE TIME
    # ----------------------------------------------

    last_telegram_alert[road_index] = (
        current_time
    )


    # ----------------------------------------------
    # INCIDENT NAME
    # ----------------------------------------------

    if detected_type == "ACCIDENT":

        emoji = "🚗💥"

        incident_text = "Vehicle Accident"

    else:

        emoji = "🧍"

        incident_text = "Person Fall"


    # ----------------------------------------------
    # MESSAGE
    # ----------------------------------------------

    message = (

        "🚨 AI TRAFFIC INCIDENT\n\n"

        f"📍 Road: "
        f"{ROAD_NAMES[road_index]}\n"

        f"⚠️ Incident: "
        f"{incident_text}\n"

        f"🎯 Confidence: "
        f"{confidence * 100:.1f}%\n\n"

        f"🔴 ROAD "
        f"{ROAD_LETTERS[road_index]} "
        f"LOCKED RED\n\n"

        "🚦 Other roads continue "
        "according to vehicle density."
    )


    print()
    print(
        "=============================================="
    )

    print(
        "SENDING TELEGRAM INCIDENT ALERT"
    )

    print(message)

    print(
        "=============================================="
    )


    send_telegram(
        message
    )


# ============================================================
# SEND INCIDENT CLEARED TELEGRAM ALERT
# ============================================================

def send_clear_alert(
    road_index
):

    message = (

        "✅ AI TRAFFIC INCIDENT CLEARED\n\n"

        f"📍 Road: "
        f"{ROAD_NAMES[road_index]}\n\n"

        f"🟢 Road "
        f"{ROAD_LETTERS[road_index]} "
        f"is released.\n\n"

        "🚦 Traffic control has returned "
        "to vehicle-density priority."
    )


    print()
    print(
        "=============================================="
    )

    print(
        "SENDING TELEGRAM CLEAR ALERT"
    )

    print(message)

    print(
        "=============================================="
    )


    send_telegram(
        message
    )


# ============================================================
# INCIDENT STATE MANAGEMENT
# ============================================================

def update_incident(
    road_index,
    incident_detected,
    detected_type,
    confidence
):

    road = ROAD_LETTERS[
        road_index
    ]


    # ========================================================
    # INCIDENT PRESENT
    # ========================================================

    if incident_detected:

        incident_clear_count[
            road_index
        ] = 0


        incident_confirm_count[
            road_index
        ] += 1


        # Keep highest confidence

        if (
            confidence
            >
            incident_confidence[
                road_index
            ]
        ):

            incident_confidence[
                road_index
            ] = confidence


        # Save incident type

        if detected_type is not None:

            incident_type[
                road_index
            ] = detected_type


        # ----------------------------------------------
        # CONFIRMED INCIDENT
        # ----------------------------------------------

        if (
            incident_confirm_count[
                road_index
            ]
            >=
            INCIDENT_CONFIRMATIONS
        ):


            if not incident_active[
                road_index
            ]:

                incident_active[
                    road_index
                ] = True


                print()
                print(
                    "########################################"
                )


                print(
                    f"🚨 INCIDENT ON "
                    f"{ROAD_NAMES[road_index]}"
                )


                print(
                    f"TYPE: "
                    f"{incident_type[road_index]}"
                )


                print(
                    f"CONFIDENCE: "
                    f"{incident_confidence[road_index]:.2f}"
                )


                print(
                    f"LOCKING ROAD {road} RED"
                )


                # ------------------------------------------
                # LOCK ROAD IN ARDUINO
                # ------------------------------------------

                send_arduino(
                    f"OFF,{road}\n"
                )


                # ------------------------------------------
                # TELEGRAM
                # ------------------------------------------

                send_incident_alert(
                    road_index,
                    incident_type[road_index],
                    incident_confidence[road_index]
                )


                print(
                    "Other roads remain active."
                )


                print(
                    "########################################"
                )


    # ========================================================
    # NO INCIDENT
    # ========================================================

    else:

        incident_confirm_count[
            road_index
        ] = 0


        if incident_active[
            road_index
        ]:

            incident_clear_count[
                road_index
            ] += 1


            if (
                incident_clear_count[
                    road_index
                ]
                >=
                INCIDENT_CLEAR_CONFIRMATIONS
            ):

                incident_active[
                    road_index
                ] = False


                incident_clear_count[
                    road_index
                ] = 0


                print()
                print(
                    f"✅ INCIDENT CLEARED "
                    f"ON {ROAD_NAMES[road_index]}"
                )


                # ------------------------------------------
                # CLEAR ARDUINO LOCK
                # ------------------------------------------

                send_arduino(
                    f"CLEAR,{road}\n"
                )


                # ------------------------------------------
                # TELEGRAM
                # ------------------------------------------

                send_clear_alert(
                    road_index
                )


                # Reset incident information

                incident_type[
                    road_index
                ] = None


                incident_confidence[
                    road_index
                ] = 0.0


# ============================================================
# MAIN LOOP
# ============================================================

print()
print("==============================================")
print("AI TRAFFIC SYSTEM STARTED")
print("==============================================")
print()
print("ROAD A = CAMERA 0")
print("ROAD B = CAMERA 1")
print("ROAD C = CAMERA 2")
print()
print("Density control: ENABLED")
print("Accident detection: ENABLED")
print("Fall detection: ENABLED")
print("Incident lock: ENABLED")
print("Telegram alerts: ENABLED")
print()


try:

    while True:

        # ====================================================
        # READ ALL CAMERAS
        # ====================================================

        for i, cap in enumerate(cameras):

            ret, frame = cap.read()


            if not ret:

                print(
                    f"{ROAD_NAMES[i]} "
                    f"camera frame failed."
                )

                continue


            # =================================================
            # VEHICLE DETECTION
            # =================================================

            vehicle_results = (
                vehicle_model.track(
                    frame,
                    persist=True,
                    classes=[2, 3, 5, 7],
                    verbose=False
                )
            )


            result = vehicle_results[0]


            # =================================================
            # VEHICLE COUNT
            # =================================================

            vehicle_count = 0


            if result.boxes is not None:

                vehicle_count = len(
                    result.boxes
                )


            vehicle_counts[i] = (
                vehicle_count
            )


            count_history[i].append(
                vehicle_count
            )


            # =================================================
            # ACCIDENT
            # =================================================

            accident_found, accident_conf = (
                detect_accident(frame)
            )


            # =================================================
            # FALL
            # =================================================

            fall_found, fall_conf = (
                detect_person_fall(frame)
            )


            # =================================================
            # DETERMINE INCIDENT TYPE
            # =================================================

            incident_detected = False

            detected_type = None

            detected_confidence = 0.0


            # Accident gets priority if both
            # are detected in the same frame.

            if accident_found:

                incident_detected = True

                detected_type = "ACCIDENT"

                detected_confidence = (
                    accident_conf
                )


            elif fall_found:

                incident_detected = True

                detected_type = "FALL"

                detected_confidence = (
                    fall_conf
                )


            # =================================================
            # UPDATE INCIDENT
            # =================================================

            update_incident(
                i,
                incident_detected,
                detected_type,
                detected_confidence
            )


            # =================================================
            # DRAW VEHICLES
            # =================================================

            annotated = result.plot()


            # =================================================
            # ROAD NAME
            # =================================================

            cv2.putText(
                annotated,
                ROAD_NAMES[i],
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (0, 255, 0),
                2
            )


            # =================================================
            # DENSITY
            # =================================================

            cv2.putText(
                annotated,
                f"Vehicles: {vehicle_count}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 0),
                2
            )


            # =================================================
            # INCIDENT DISPLAY
            # =================================================

            if accident_found:

                cv2.putText(
                    annotated,
                    f"ACCIDENT "
                    f"{accident_conf:.2f}",
                    (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 0, 255),
                    2
                )


            elif fall_found:

                cv2.putText(
                    annotated,
                    f"PERSON FALL "
                    f"{fall_conf:.2f}",
                    (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 0, 255),
                    2
                )


            elif incident_active[i]:

                cv2.putText(
                    annotated,
                    "INCIDENT LOCKED",
                    (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 0, 255),
                    2
                )


            else:

                cv2.putText(
                    annotated,
                    "STATUS: NORMAL",
                    (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 0),
                    2
                )


            # =================================================
            # TRAFFIC LIGHT STATUS
            # =================================================

            if incident_active[i]:

                cv2.putText(
                    annotated,
                    "TRAFFIC LIGHT: RED LOCK",
                    (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.60,
                    (0, 0, 255),
                    2
                )

            else:

                cv2.putText(
                    annotated,
                    "TRAFFIC LIGHT: DENSITY CONTROL",
                    (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 0),
                    2
                )


            # =================================================
            # SHOW
            # =================================================

            cv2.imshow(
                ROAD_NAMES[i],
                annotated
            )


        # ====================================================
        # DENSITY DECISION
        # ====================================================

        if (
            time.time()
            -
            last_density_update
            >=
            DENSITY_UPDATE_TIME
        ):

            # =================================================
            # CALCULATE AVERAGE DENSITY
            # =================================================

            average_density = []


            for i in range(3):

                if len(
                    count_history[i]
                ) > 0:

                    average = (
                        sum(
                            count_history[i]
                        )
                        /
                        len(
                            count_history[i]
                        )
                    )

                else:

                    average = 0


                average_density.append(
                    average
                )


            # =================================================
            # SORT ROADS BY DENSITY
            # =================================================

            sorted_roads = sorted(
                range(3),
                key=lambda x:
                    average_density[x],
                reverse=True
            )


            # =================================================
            # PRINT DENSITY
            # =================================================

            print()
            print(
                "=============================================="
            )

            print(
                "CURRENT TRAFFIC DENSITY"
            )

            print(
                f"ROAD A : "
                f"{average_density[0]:.1f}"
            )

            print(
                f"ROAD B : "
                f"{average_density[1]:.1f}"
            )

            print(
                f"ROAD C : "
                f"{average_density[2]:.1f}"
            )


            # =================================================
            # REMOVE INCIDENT ROADS FROM PRIORITY
            # =================================================

            available_roads = []

            locked_roads = []


            for road_index in sorted_roads:

                if incident_active[
                    road_index
                ]:

                    locked_roads.append(
                        ROAD_LETTERS[
                            road_index
                        ]
                    )

                else:

                    available_roads.append(
                        ROAD_LETTERS[
                            road_index
                        ]
                    )


            # =================================================
            # DISPLAY LOCKED ROADS
            # =================================================

            print(
                "----------------------------------------------"
            )


            print(
                "LOCKED ROADS:",
                locked_roads
            )


            print(
                "AVAILABLE ROADS:",
                available_roads
            )


            # =================================================
            # BUILD DENSITY PRIORITY
            # =================================================

            if len(
                available_roads
            ) == 3:

                priority = available_roads

                times = [
                    FIRST_PRIORITY_TIME,
                    SECOND_PRIORITY_TIME,
                    THIRD_PRIORITY_TIME
                ]


            elif len(
                available_roads
            ) == 2:

                priority = available_roads

                times = [
                    FIRST_PRIORITY_TIME,
                    SECOND_PRIORITY_TIME
                ]


            elif len(
                available_roads
            ) == 1:

                priority = available_roads

                times = [
                    FIRST_PRIORITY_TIME
                ]


            else:

                priority = []

                times = []


            # =================================================
            # SEND PRIORITY
            # =================================================

            if len(priority) == 3:

                command = (
                    f"{priority[0]}15,"
                    f"{priority[1]}10,"
                    f"{priority[2]}05\n"
                )


                print(
                    f"DENSITY PRIORITY: "
                    f"{priority[0]} > "
                    f"{priority[1]} > "
                    f"{priority[2]}"
                )


                send_arduino(
                    command
                )


            elif len(priority) == 2:

                command = (
                    f"{priority[0]}15,"
                    f"{priority[1]}10,"
                    f"{priority[1]}10\n"
                )


                print(
                    f"DENSITY PRIORITY: "
                    f"{priority[0]} > "
                    f"{priority[1]}"
                )


                send_arduino(
                    command
                )


            elif len(priority) == 1:

                command = (
                    f"{priority[0]}15,"
                    f"{priority[0]}15,"
                    f"{priority[0]}15\n"
                )


                print(
                    f"ONLY AVAILABLE ROAD: "
                    f"{priority[0]}"
                )


                send_arduino(
                    command
                )


            else:

                print(
                    "🚨 ALL ROADS INCIDENT LOCKED"
                )


            # =================================================
            # RESET DENSITY HISTORY
            # =================================================

            count_history = [
                [],
                [],
                []
            ]


            last_density_update = (
                time.time()
            )


            print(
                "=============================================="
            )


        # ====================================================
        # QUIT
        # ====================================================

        if (
            cv2.waitKey(1)
            &
            0xFF
        ) == ord("q"):

            break


# ============================================================
# CLEANUP
# ============================================================

except KeyboardInterrupt:

    print(
        "System interrupted."
    )


finally:

    for cap in cameras:

        cap.release()


    cv2.destroyAllWindows()


    try:

        arduino.close()

    except:

        pass


    print(
        "AI traffic system stopped."
    )
