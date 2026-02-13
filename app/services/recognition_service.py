import cv2
import os
import numpy as np

def train_model(data_path="data/registered_faces"):
    faces = []
    labels = []
    label_map = {}
    label_id = 0

    for roll_no in os.listdir(data_path):
        student_path = os.path.join(data_path, roll_no)
        if not os.path.isdir(student_path):
            continue

        label_map[label_id] = roll_no

        for img_name in os.listdir(student_path):
            img_path = os.path.join(student_path, img_name)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

            if img is None:
                continue

            faces.append(img)
            labels.append(label_id)

        label_id += 1

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))

    return recognizer, label_map


def recognize_face():
    recognizer, label_map = train_model()

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    cap = cv2.VideoCapture(0)

    recognized_rolls = set()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            label, confidence = recognizer.predict(face)

            roll_no = label_map.get(label)

            if confidence < 80:
                recognized_rolls.add(roll_no)
                text = f"{roll_no}"
            else:
                text = "Unknown"

            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
            cv2.putText(frame, text, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

        cv2.imshow("Attendance - Press Q to Stop", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    return list(recognized_rolls)
