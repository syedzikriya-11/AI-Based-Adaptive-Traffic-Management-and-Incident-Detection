
# ============================================================
# AI 3-ROAD TRAFFIC MANAGEMENT
# AI + TELEGRAM ALERTS + TELEGRAM MANUAL CONTROL
#
# OPTIMIZED FOR CPU / INTEL ARC SYSTEMS
#
# CAMERA MAPPING:
# ROAD A = CAMERA 3  (EXTERNAL CAMERA)
# ROAD B = CAMERA 1
# ROAD C = CAMERA 2
#
# FEATURES:
# 1. AI vehicle detection
# 2. Traffic density control
# 3. Accident detection
# 4. Person fall detection
# 5. Incident confirmation
# 6. Incident RED LOCK
# 7. Telegram incident alerts
# 8. Separate Telegram manual-control bot
# 9. AUTO / MANUAL modes
# 10. Road A/B/C manual control
# 11. RED / YELLOW / GREEN control
# 12. ALL RED emergency control
# 13. Secure Telegram Chat ID authorization
# 14. AI continues detection during MANUAL mode
# ============================================================


import cv2
import time
import serial
import requests
import threading

from ultralytics import YOLO


# ============================================================
# TELEGRAM ALERT BOT
# ============================================================

TELEGRAM_ALERT_BOT_TOKEN = "8749363566:AAG9h_bP977c4dKZc_2xd2K87sXVQI9N1vE"
TELEGRAM_CHAT_ID = "8676102201"


# ============================================================
# TELEGRAM CONTROL BOT
# ============================================================
# Create a SECOND bot using @BotFather.
# Put its token here.

TELEGRAM_CONTROL_BOT_TOKEN = "8942408366:AAHrHMc_XwDDf_et-0pKcxZ2zftT-KL9yPc"

# Only this Chat ID can control the signals.
AUTHORIZED_CONTROL_CHAT_ID = "8676102201"


# ============================================================
# MODEL FILES
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
CAMERA_BUFFER_SIZE = 1


# ============================================================
# CAMERA MAPPING
# ============================================================

# ROAD A -> External Camera -> Index 3
# ROAD B -> Camera Index 1
# ROAD C -> Camera Index 2

CAMERA_INDICES = [3, 1, 2]


# ============================================================
# PERFORMANCE SETTINGS
# ============================================================

YOLO_IMAGE_SIZE = 320

VEHICLE_FRAME_SKIP = 3
ACCIDENT_FRAME_SKIP = 8
FALL_FRAME_SKIP = 8


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

INCIDENT_CONFIRMATIONS = 5
INCIDENT_CLEAR_CONFIRMATIONS = 50


# ============================================================
# TELEGRAM SETTINGS
# ============================================================

TELEGRAM_COOLDOWN = 30
TELEGRAM_POLL_INTERVAL = 2


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
# GLOBAL CONTROL STATE
# ============================================================

# AUTO:
# AI controls traffic signals.

# MANUAL:
# Telegram operator controls traffic signals.

CONTROL_MODE = "AUTO"

CONTROL_LOCK = threading.Lock()

MANUAL_SELECTED_ROAD = 0

MANUAL_SIGNAL = [
    "RED",
    "RED",
    "RED"
]

CURRENT_SIGNAL_STATE = [
    "RED",
    "RED",
    "RED"
]

LAST_ARDUINO_COMMAND = ""


# ============================================================
# LOAD VEHICLE MODEL
# ============================================================

print()
print("==============================================")
print("LOADING VEHICLE MODEL")
print("==============================================")

vehicle_model = YOLO(VEHICLE_MODEL)

print("Vehicle model loaded.")


# ============================================================
# LOAD ACCIDENT MODEL
# ============================================================

print()
print("==============================================")
print("LOADING ACCIDENT MODEL")
print("==============================================")

accident_model = YOLO(ACCIDENT_MODEL)

print("Accident model loaded.")
print("Accident classes:", accident_model.names)


# ============================================================
# LOAD FALL DETECTION MODEL
# ============================================================

print()
print("==============================================")
print("LOADING FALL DETECTION MODEL")
print("==============================================")

pose_model = YOLO(POSE_MODEL)

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

    time.sleep(2)

    print(
        f"Arduino connected: {ARDUINO_PORT}"
    )

except Exception as e:

    print("Arduino connection failed.")
    print(e)

    raise SystemExit


# ============================================================
# CAMERA CLASS
# ============================================================

class CameraStream:

    def __init__(self, camera_index):

        self.camera_index = camera_index

        self.cap = cv2.VideoCapture(
            camera_index,
            cv2.CAP_DSHOW
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            CAMERA_WIDTH
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            CAMERA_HEIGHT
        )

        self.cap.set(
            cv2.CAP_PROP_BUFFERSIZE,
            CAMERA_BUFFER_SIZE
        )

        self.frame = None

        self.running = False

        self.lock = threading.Lock()


    def start(self):

        self.running = True

        thread = threading.Thread(
            target=self.update,
            daemon=True
        )

        thread.start()

        return self


    def update(self):

        while self.running:

            ret, frame = self.cap.read()

            if ret:

                with self.lock:

                    self.frame = frame


    def read(self):

        with self.lock:

            if self.frame is None:

                return False, None

            return True, self.frame.copy()


    def stop(self):

        self.running = False

        time.sleep(0.2)

        self.cap.release()


# ============================================================
# OPEN CAMERAS
# ============================================================

print()
print("==============================================")
print("OPENING CAMERAS")
print("==============================================")

cameras = []


for road_index, camera_index in enumerate(CAMERA_INDICES):

    print(
        f"Opening Camera {camera_index} "
        f"-> {ROAD_NAMES[road_index]}"
    )

    camera = CameraStream(
        camera_index
    )

    if camera.cap.isOpened():

        print(
            f"{ROAD_NAMES[road_index]} camera OK"
        )

        camera.start()

    else:

        print(
            f"WARNING: "
            f"{ROAD_NAMES[road_index]} "
            f"camera not available"
        )

    cameras.append(camera)


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

incident_type = [
    None,
    None,
    None
]

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

count_history = [
    [],
    [],
    []
]


# ============================================================
# LAST DETECTION RESULTS
# ============================================================

last_accident_found = [
    False,
    False,
    False
]

last_accident_conf = [
    0.0,
    0.0,
    0.0
]

last_fall_found = [
    False,
    False,
    False
]

last_fall_conf = [
    0.0,
    0.0,
    0.0
]


# ============================================================
# FRAME COUNTERS
# ============================================================

frame_counters = [
    0,
    0,
    0
]


# ============================================================
# TIME
# ============================================================

last_density_update = time.time()


# ============================================================
# SEND TO ARDUINO
# ============================================================

def send_arduino(command):

    global LAST_ARDUINO_COMMAND

    try:

        # Avoid sending identical commands repeatedly.

        if command == LAST_ARDUINO_COMMAND:

            return

        arduino.write(
            command.encode()
        )

        LAST_ARDUINO_COMMAND = command

        print(
            f"ARDUINO << {command.strip()}"
        )

    except Exception as e:

        print(
            "Arduino communication error:",
            e
        )


# ============================================================
# FORCE ARDUINO COMMAND
# ============================================================

def force_arduino(command):

    global LAST_ARDUINO_COMMAND

    try:

        arduino.write(
            command.encode()
        )

        LAST_ARDUINO_COMMAND = command

        print(
            f"ARDUINO << {command.strip()}"
        )

    except Exception as e:

        print(
            "Arduino communication error:",
            e
        )


# ============================================================
# TELEGRAM ALERT FUNCTION
# ============================================================

def send_telegram(message):

    if (
        TELEGRAM_ALERT_BOT_TOKEN == ""
        or
        TELEGRAM_ALERT_BOT_TOKEN == "YOUR_BOT_TOKEN"
    ):

        print(
            "WARNING: Telegram alert bot token "
            "not configured."
        )

        return False


    if (
        TELEGRAM_CHAT_ID == ""
        or
        TELEGRAM_CHAT_ID == "YOUR_CHAT_ID"
    ):

        print(
            "WARNING: Telegram Chat ID "
            "not configured."
        )

        return False


    # Correct Telegram API URL.

    url = (
        "https://api.telegram.org/bot"
        + TELEGRAM_ALERT_BOT_TOKEN
        + "/sendMessage"
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
                "TELEGRAM ALERT SENT"
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
# ACCIDENT DETECTION
# ============================================================

def detect_accident(frame):

    results = accident_model(
        frame,
        imgsz=YOLO_IMAGE_SIZE,
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

            if confidence >= ACCIDENT_CONFIDENCE:

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
        imgsz=YOLO_IMAGE_SIZE,
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


        if confidence < PERSON_CONFIDENCE:

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


        if aspect_ratio < 1.20:

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


    last_telegram_alert[road_index] = (
        current_time
    )


    if detected_type == "ACCIDENT":

        incident_text = "Vehicle Accident"

    else:

        incident_text = "Person Fall"


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


    send_telegram(message)


# ============================================================
# SEND INCIDENT CLEARED TELEGRAM ALERT
# ============================================================

def send_clear_alert(road_index):

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


    send_telegram(message)


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


        if detected_type is not None:

            incident_type[
                road_index
            ] = detected_type


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
                    f"INCIDENT ON "
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


                # Incident road is forced RED.

                force_arduino(
                    f"OFF,{road}\n"
                )


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
                    f"INCIDENT CLEARED "
                    f"ON {ROAD_NAMES[road_index]}"
                )


                force_arduino(
                    f"CLEAR,{road}\n"
                )


                send_clear_alert(
                    road_index
                )


                incident_type[
                    road_index
                ] = None


                incident_confidence[
                    road_index
                ] = 0.0


# ============================================================
# CONTROL MODE
# ============================================================

def set_manual_mode():

    global CONTROL_MODE
    global MANUAL_SIGNAL
    global CURRENT_SIGNAL_STATE

    with CONTROL_LOCK:

        CONTROL_MODE = "MANUAL"

        # Safety state: when MANUAL is selected,
        # all three roads must start RED.
        MANUAL_SIGNAL = [
            "RED",
            "RED",
            "RED"
        ]

        CURRENT_SIGNAL_STATE = [
            "RED",
            "RED",
            "RED"
        ]


    print()
    print("==============================================")
    print("TELEGRAM: MANUAL MODE ENABLED")
    print("ALL ROADS FORCED RED")
    print("AI SIGNAL CONTROL DISABLED")
    print("==============================================")


    # Tell Arduino that manual mode is active.
    force_arduino(
        "MANUAL_MODE\n"
    )

    # Immediately force ALL traffic lights RED.
    # This prevents the previous AUTO state from
    # remaining active or toggling Road A.
    time.sleep(0.05)

    force_arduino(
        "ALL_RED\n"
    )


# ============================================================
# RETURN TO AUTO
# ============================================================

def set_auto_mode():

    global CONTROL_MODE

    with CONTROL_LOCK:

        CONTROL_MODE = "AUTO"


    print()
    print("==============================================")
    print("AI AUTO MODE ENABLED")
    print("TELEGRAM MANUAL CONTROL DISABLED")
    print("==============================================")


    force_arduino(
        "AUTO_MODE\n"
    )


# ============================================================
# MANUAL ALL RED
# ============================================================

def manual_all_red():

    global MANUAL_SIGNAL
    global CURRENT_SIGNAL_STATE

    with CONTROL_LOCK:

        MANUAL_SIGNAL = [
            "RED",
            "RED",
            "RED"
        ]

        CURRENT_SIGNAL_STATE = [
            "RED",
            "RED",
            "RED"
        ]


    force_arduino(
        "ALL_RED\n"
    )


    print()
    print("##############################################")
    print("TELEGRAM MANUAL: ALL ROADS RED")
    print("##############################################")


# ============================================================
# MANUAL SIGNAL
# ============================================================

def manual_signal(
    road_index,
    signal
):

    global MANUAL_SIGNAL
    global CURRENT_SIGNAL_STATE

    signal = signal.upper()


    if signal not in [
        "RED",
        "YELLOW",
        "GREEN"
    ]:

        return False, "Invalid signal."


    # ========================================================
    # ONLY MANUAL MODE CAN USE THIS
    # ========================================================

    with CONTROL_LOCK:

        if CONTROL_MODE != "MANUAL":

            return (
                False,
                "Manual mode is not active."
            )


    # ========================================================
    # INCIDENT SAFETY LOCK
    # ========================================================

    if (
        signal == "GREEN"
        and
        incident_active[road_index]
    ):

        return (
            False,
            f"ROAD {ROAD_LETTERS[road_index]} "
            "is incident locked."
        )


    # ========================================================
    # GREEN SAFETY
    # ========================================================
    # Do not allow multiple GREEN roads.

    if signal == "GREEN":

        for i in range(3):

            if i != road_index:

                MANUAL_SIGNAL[i] = "RED"

                CURRENT_SIGNAL_STATE[i] = "RED"


    MANUAL_SIGNAL[road_index] = signal

    CURRENT_SIGNAL_STATE[road_index] = signal


    road = ROAD_LETTERS[road_index]


    command = (
        f"MANUAL,{road},{signal}\n"
    )


    force_arduino(command)


    print()
    print(
        f"TELEGRAM MANUAL: "
        f"ROAD {road} -> {signal}"
    )


    return (
        True,
        f"ROAD {road} set to {signal}."
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

def get_system_status():

    with CONTROL_LOCK:

        mode = CONTROL_MODE

    lines = []

    lines.append(
        "🚦 AI TRAFFIC SYSTEM"
    )

    lines.append("")

    if mode == "AUTO":

        lines.append(
            "Mode: 🟢 AUTO"
        )

    else:

        lines.append(
            "Mode: 🟠 MANUAL"
        )


    lines.append("")


    for i in range(3):

        if incident_active[i]:

            status = "🔴 INCIDENT LOCK"

        else:

            status = CURRENT_SIGNAL_STATE[i]

            if status == "GREEN":

                status = "🟢 GREEN"

            elif status == "YELLOW":

                status = "🟡 YELLOW"

            else:

                status = "🔴 RED"


        lines.append(
            f"{ROAD_NAMES[i]}: {status}"
        )


    lines.append("")


    for i in range(3):

        lines.append(
            f"{ROAD_NAMES[i]} vehicles: "
            f"{vehicle_counts[i]}"
        )


    return "\n".join(lines)


# ============================================================
# TELEGRAM CONTROL KEYBOARD
# ============================================================

def control_keyboard():

    return {

        "inline_keyboard": [

            [
                {
                    "text": "🟢 AUTO MODE",
                    "callback_data": "AUTO"
                },

                {
                    "text": "🟠 MANUAL MODE",
                    "callback_data": "MANUAL"
                }
            ],

            [
                {
                    "text": "🅰️ ROAD A",
                    "callback_data": "ROAD_0"
                },

                {
                    "text": "🅱️ ROAD B",
                    "callback_data": "ROAD_1"
                },

                {
                    "text": "🅲️ ROAD C",
                    "callback_data": "ROAD_2"
                }
            ],

            [
                {
                    "text": "🚨 ALL RED",
                    "callback_data": "ALL_RED"
                }
            ],

            [
                {
                    "text": "📊 SYSTEM STATUS",
                    "callback_data": "STATUS"
                }
            ]
        ]
    }


# ============================================================
# SIGNAL KEYBOARD
# ============================================================

def signal_keyboard(road_index):

    return {

        "inline_keyboard": [

            [
                {
                    "text": "🔴 RED",
                    "callback_data":
                        f"SIG_{road_index}_RED"
                },

                {
                    "text": "🟡 YELLOW",
                    "callback_data":
                        f"SIG_{road_index}_YELLOW"
                },

                {
                    "text": "🟢 GREEN",
                    "callback_data":
                        f"SIG_{road_index}_GREEN"
                }
            ],

            [
                {
                    "text": "◀️ BACK",
                    "callback_data": "BACK"
                }
            ]
        ]
    }


# ============================================================
# TELEGRAM API
# ============================================================

def telegram_api(
    method,
    data=None
):

    if (
        TELEGRAM_CONTROL_BOT_TOKEN == ""
        or
        TELEGRAM_CONTROL_BOT_TOKEN
        == "YOUR_CONTROL_BOT_TOKEN"
    ):

        return None


    url = (
        "https://api.telegram.org/bot"
        +
        TELEGRAM_CONTROL_BOT_TOKEN
        +
        "/"
        +
        method
    )


    try:

        # IMPORTANT:
        # Telegram getUpdates uses long polling.
        # If Telegram waits 20 seconds, the HTTP request
        # must wait LONGER than 20 seconds.
        if method == "getUpdates":

            request_timeout = (
                5,
                35
            )

        else:

            request_timeout = (
                5,
                15
            )


        response = requests.post(
            url,
            data=data,
            timeout=request_timeout
        )


        if response.status_code != 200:

            print(
                "Telegram control API error:",
                response.status_code,
                response.text
            )

            return None


        result = response.json()

        if not result.get("ok", False):

            print(
                "Telegram control API returned error:",
                result
            )

            return None


        return result


    except requests.exceptions.Timeout:

        # Telegram/network timeout must NEVER stop
        # the AI traffic processing loop.
        if method == "getUpdates":

            print(
                "Telegram polling timeout - "
                "retrying control bot..."
            )

        else:

            print(
                f"Telegram {method} timeout - "
                "control command may need retry."
            )

        return None


    except requests.exceptions.ConnectionError as e:

        print(
            "Telegram control connection error - "
            "retrying:",
            e
        )

        return None


    except Exception as e:

        print(
            "Telegram control API error:",
            e
        )

        return None


# ============================================================
# SEND CONTROL MESSAGE
# ============================================================

def send_control_message(
    chat_id,
    text,
    keyboard=None
):

    data = {

        "chat_id": chat_id,

        "text": text
    }


    if keyboard is not None:

        import json

        data["reply_markup"] = json.dumps(
            keyboard
        )


    return telegram_api(
        "sendMessage",
        data
    )


# ============================================================
# ANSWER CALLBACK
# ============================================================

def answer_callback(
    callback_id,
    text
):

    return telegram_api(
        "answerCallbackQuery",
        {
            "callback_query_id":
                callback_id,

            "text": text,

            "show_alert": False
        }
    )


# ============================================================
# TELEGRAM CONTROL BOT
# ============================================================

def telegram_control_loop():

    global MANUAL_SELECTED_ROAD

    print()
    print("==============================================")
    print("TELEGRAM CONTROL BOT")
    print("==============================================")


    if (
        TELEGRAM_CONTROL_BOT_TOKEN == ""
        or
        TELEGRAM_CONTROL_BOT_TOKEN
        == "YOUR_CONTROL_BOT_TOKEN"
    ):

        print(
            "Control bot token not configured."
        )

        print(
            "Telegram manual control disabled."
        )

        return


    print(
        "Telegram manual control enabled."
    )

    print(
        "Authorized Chat ID:",
        AUTHORIZED_CONTROL_CHAT_ID
    )

    # --------------------------------------------------------
    # VERIFY CONTROL BOT BEFORE STARTING POLLING
    # --------------------------------------------------------
    # This gives a clear error if the token is wrong and also
    # removes an old webhook. getUpdates cannot work while a
    # webhook is active.
    bot_info = telegram_api("getMe", {})

    if not bot_info:

        print()
        print("❌ CONTROL BOT CHECK FAILED")
        print("Check TELEGRAM_CONTROL_BOT_TOKEN.")
        print("Telegram manual control will not work.")
        return

    bot_user = bot_info.get("result", {})

    print(
        "Control Bot:",
        "@" + bot_user.get("username", "unknown")
    )

    # Force polling mode.
    webhook_result = telegram_api(
        "deleteWebhook",
        {
            "drop_pending_updates": False
        }
    )

    if webhook_result:

        print(
            "Telegram webhook disabled - polling mode ready."
        )

    print(
        "Waiting for /start or /control messages..."
    )

    offset = 0


    while True:

        try:

            result = telegram_api(
                "getUpdates",
                {
                    # Telegram long-polling timeout.
                    # telegram_api() HTTP timeout is 35 seconds,
                    # so it will not expire before this 20-second wait.
                    "timeout": 20,
                    "offset": offset,
                    "allowed_updates":
                        '["message","callback_query"]'
                }
            )


            if not result:

                time.sleep(
                    TELEGRAM_POLL_INTERVAL
                )

                continue


            updates = result.get(
                "result",
                []
            )


            for update in updates:

                offset = (
                    update["update_id"] + 1
                )


                # =================================================
                # NORMAL MESSAGE
                # =================================================

                if "message" in update:

                    message = update[
                        "message"
                    ]

                    chat_id = str(
                        message["chat"]["id"]
                    )

                    text = message.get(
                        "text",
                        ""
                    ).strip().lower()


                    # SECURITY

                    if (
                        chat_id
                        !=
                        AUTHORIZED_CONTROL_CHAT_ID
                    ):

                        send_control_message(
                            chat_id,
                            "⛔ Unauthorized user."
                        )

                        continue


                    if text in [
                        "/start",
                        "/control",
                        "/menu"
                    ]:

                        send_control_message(
                            chat_id,
                            get_system_status()
                            +
                            "\n\nSelect control:",
                            control_keyboard()
                        )


                    elif text == "/status":

                        send_control_message(
                            chat_id,
                            get_system_status(),
                            control_keyboard()
                        )


                    elif text == "/auto":

                        set_auto_mode()

                        send_control_message(
                            chat_id,
                            "🟢 AI AUTO MODE ENABLED\n\n"
                            "AI now controls the traffic signals.",
                            control_keyboard()
                        )


                    elif text == "/manual":

                        set_manual_mode()

                        send_control_message(
                            chat_id,
                            "🟠 MANUAL MODE ENABLED\n\n"
                            "Select a road:",
                            control_keyboard()
                        )


                    elif text == "/allred":

                        manual_all_red()

                        send_control_message(
                            chat_id,
                            "🚨 ALL ROADS RED",
                            control_keyboard()
                        )


                    else:

                        send_control_message(
                            chat_id,
                            "Use /control to open "
                            "traffic control.",
                            control_keyboard()
                        )


                # =================================================
                # INLINE BUTTON
                # =================================================

                if "callback_query" in update:

                    callback = update[
                        "callback_query"
                    ]

                    callback_id = callback[
                        "id"
                    ]

                    data = callback.get(
                        "data",
                        ""
                    )

                    callback_message = (
                        callback.get(
                            "message",
                            {}
                        )
                    )

                    chat = callback_message.get(
                        "chat",
                        {}
                    )

                    chat_id = str(
                        chat.get(
                            "id",
                            ""
                        )
                    )


                    # SECURITY

                    if (
                        chat_id
                        !=
                        AUTHORIZED_CONTROL_CHAT_ID
                    ):

                        answer_callback(
                            callback_id,
                            "Unauthorized."
                        )

                        continue


                    # =================================================
                    # AUTO
                    # =================================================

                    if data == "AUTO":

                        set_auto_mode()

                        answer_callback(
                            callback_id,
                            "AI AUTO MODE enabled"
                        )

                        send_control_message(
                            chat_id,
                            "🟢 AUTO MODE\n\n"
                            "AI controls the signals.",
                            control_keyboard()
                        )


                    # =================================================
                    # MANUAL
                    # =================================================

                    elif data == "MANUAL":

                        set_manual_mode()

                        answer_callback(
                            callback_id,
                            "Manual mode enabled"
                        )

                        send_control_message(
                            chat_id,
                            "🟠 MANUAL MODE\n\n"
                            "Select a road:",
                            control_keyboard()
                        )


                    # =================================================
                    # ROAD SELECTION
                    # =================================================

                    elif data.startswith(
                        "ROAD_"
                    ):

                        try:

                            road_index = int(
                                data.split("_")[1]
                            )

                            if road_index not in [
                                0,
                                1,
                                2
                            ]:

                                raise ValueError


                            with CONTROL_LOCK:

                                if (
                                    CONTROL_MODE
                                    !=
                                    "MANUAL"
                                ):

                                    answer_callback(
                                        callback_id,
                                        "Enable MANUAL mode first."
                                    )

                                    continue


                            MANUAL_SELECTED_ROAD = (
                                road_index
                            )


                            answer_callback(
                                callback_id,
                                f"{ROAD_NAMES[road_index]} selected"
                            )


                            send_control_message(
                                chat_id,
                                f"🚦 {ROAD_NAMES[road_index]}\n\n"
                                f"Select signal:",
                                signal_keyboard(
                                    road_index
                                )
                            )


                        except Exception:

                            answer_callback(
                                callback_id,
                                "Invalid road."
                            )


                    # =================================================
                    # SIGNAL
                    # =================================================

                    elif data.startswith(
                        "SIG_"
                    ):

                        parts = data.split("_")


                        if len(parts) != 3:

                            answer_callback(
                                callback_id,
                                "Invalid command."
                            )

                            continue


                        road_index = int(
                            parts[1]
                        )

                        signal = parts[2]


                        success, message = (
                            manual_signal(
                                road_index,
                                signal
                            )
                        )


                        answer_callback(
                            callback_id,
                            message
                        )


                        send_control_message(
                            chat_id,
                            (
                                "✅ "
                                if success
                                else
                                "⚠️ "
                            )
                            +
                            message,
                            signal_keyboard(
                                road_index
                            )
                        )


                    # =================================================
                    # ALL RED
                    # =================================================

                    elif data == "ALL_RED":

                        manual_all_red()

                        answer_callback(
                            callback_id,
                            "All roads RED"
                        )

                        send_control_message(
                            chat_id,
                            "🚨 ALL ROADS RED",
                            control_keyboard()
                        )


                    # =================================================
                    # STATUS
                    # =================================================

                    elif data == "STATUS":

                        answer_callback(
                            callback_id,
                            "Status updated"
                        )

                        send_control_message(
                            chat_id,
                            get_system_status(),
                            control_keyboard()
                        )


                    # =================================================
                    # BACK
                    # =================================================

                    elif data == "BACK":

                        answer_callback(
                            callback_id,
                            "Back"
                        )

                        send_control_message(
                            chat_id,
                            get_system_status()
                            +
                            "\n\nSelect control:",
                            control_keyboard()
                        )


        except Exception as e:

            print(
                "Telegram control loop error:",
                e
            )

            time.sleep(3)


# ============================================================
# START TELEGRAM CONTROL THREAD
# ============================================================

telegram_thread = threading.Thread(
    target=telegram_control_loop,
    daemon=True
)

telegram_thread.start()


# ============================================================
# MAIN LOOP
# ============================================================

print()
print("==============================================")
print("AI TRAFFIC SYSTEM STARTED")
print("==============================================")

print()

print(
    "ROAD A = CAMERA 3 (EXTERNAL CAMERA)"
)

print(
    "ROAD B = CAMERA 1"
)

print(
    "ROAD C = CAMERA 2"
)

print()

print(
    "Density control: ENABLED"
)

print(
    "Accident detection: ENABLED"
)

print(
    "Fall detection: ENABLED"
)

print(
    "Incident lock: ENABLED"
)

print(
    "Telegram alerts: ENABLED"
)

print(
    "Telegram manual control: ENABLED"
)

print()

print(
    "Performance mode: OPTIMIZED"
)

print(
    f"YOLO image size: {YOLO_IMAGE_SIZE}"
)

print()


try:

    while True:

        # ====================================================
        # PROCESS EACH CAMERA
        # ====================================================

        for i, camera in enumerate(cameras):

            ret, frame = camera.read()


            if not ret:

                continue


            # =================================================
            # FRAME COUNTER
            # =================================================

            frame_counters[i] += 1

            current_frame = (
                frame_counters[i]
            )


            # =================================================
            # VEHICLE DETECTION
            # =================================================

            if (
                current_frame
                %
                VEHICLE_FRAME_SKIP
                ==
                0
            ):

                vehicle_results = (
                    vehicle_model.predict(
                        frame,
                        imgsz=YOLO_IMAGE_SIZE,
                        classes=[2, 3, 5, 7],
                        verbose=False
                    )
                )


                result = vehicle_results[0]


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


                annotated = result.plot()


            else:

                vehicle_count = (
                    vehicle_counts[i]
                )

                annotated = frame.copy()


            # =================================================
            # ACCIDENT DETECTION
            # =================================================

            if (
                current_frame
                %
                ACCIDENT_FRAME_SKIP
                ==
                0
            ):

                (
                    accident_found,
                    accident_conf
                ) = detect_accident(
                    frame
                )


                last_accident_found[i] = (
                    accident_found
                )

                last_accident_conf[i] = (
                    accident_conf
                )


            else:

                accident_found = (
                    last_accident_found[i]
                )

                accident_conf = (
                    last_accident_conf[i]
                )


            # =================================================
            # FALL DETECTION
            # =================================================

            if (
                current_frame
                %
                FALL_FRAME_SKIP
                ==
                0
            ):

                (
                    fall_found,
                    fall_conf
                ) = detect_person_fall(
                    frame
                )


                last_fall_found[i] = (
                    fall_found
                )

                last_fall_conf[i] = (
                    fall_conf
                )


            else:

                fall_found = (
                    last_fall_found[i]
                )

                fall_conf = (
                    last_fall_conf[i]
                )


            # =================================================
            # DETERMINE INCIDENT
            # =================================================

            incident_detected = False

            detected_type = None

            detected_confidence = 0.0


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

            if (
                current_frame
                %
                min(
                    ACCIDENT_FRAME_SKIP,
                    FALL_FRAME_SKIP
                )
                ==
                0
            ):

                update_incident(
                    i,
                    incident_detected,
                    detected_type,
                    detected_confidence
                )


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
            # VEHICLE COUNT
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
            # CONTROL MODE DISPLAY
            # =================================================

            with CONTROL_LOCK:

                current_mode = CONTROL_MODE


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


            elif current_mode == "MANUAL":

                cv2.putText(
                    annotated,
                    "CONTROL: TELEGRAM MANUAL",
                    (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 165, 255),
                    2
                )


            else:

                cv2.putText(
                    annotated,
                    "CONTROL: AI AUTO",
                    (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.60,
                    (0, 255, 0),
                    2
                )


            # =================================================
            # MANUAL MODE INFORMATION
            # =================================================

            if current_mode == "MANUAL":

                cv2.putText(
                    annotated,
                    "REMOTE CONTROL ACTIVE",
                    (20, 175),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.50,
                    (0, 165, 255),
                    2
                )


            # =================================================
            # SHOW CAMERA
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
            # SORT ROADS
            # =================================================

            sorted_roads = sorted(
                range(3),
                key=lambda x:
                    average_density[x],
                reverse=True
            )


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
            # REMOVE INCIDENT ROADS
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
            # AI SIGNAL CONTROL
            # =================================================

            with CONTROL_LOCK:

                current_mode = CONTROL_MODE


            if current_mode == "AUTO":

                if len(available_roads) == 3:

                    priority = available_roads


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


                elif len(available_roads) == 2:

                    priority = available_roads


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


                elif len(available_roads) == 1:

                    priority = available_roads


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
                        "ALL ROADS INCIDENT LOCKED"
                    )


            else:

                print(
                    "MANUAL MODE ACTIVE - "
                    "AI SIGNAL CONTROL BYPASSED"
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
        # KEYBOARD EXIT
        # ====================================================

        key = cv2.waitKey(1) & 0xFF


        if key == ord("q"):

            break


# ============================================================
# CLEANUP
# ============================================================

except KeyboardInterrupt:

    print(
        "System interrupted."
    )


finally:

    # ========================================================
    # SAFETY: ALL RED BEFORE SHUTDOWN
    # ========================================================

    try:

        force_arduino(
            "ALL_RED\n"
        )

    except:

        pass


    # ========================================================
    # STOP CAMERAS
    # ========================================================

    for camera in cameras:

        camera.stop()


    cv2.destroyAllWindows()


    try:

        arduino.close()

    except:

        pass


    print(
        "AI traffic system stopped."
    )

