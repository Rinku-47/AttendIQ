import cv2
import os

def capture_faces(roll_no):
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    save_path = f"data/registered_faces/{roll_no}"
    os.makedirs(save_path, exist_ok=True)

    cap = cv2.VideoCapture(0)
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            count += 1
            face = gray[y:y+h, x:x+w]
            cv2.imwrite(f"{save_path}/{count}.jpg", face)
            cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)

        cv2.imshow("Register Face - Press Q to Stop", frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or count >= 20:
            break

    cap.release()
    cv2.destroyAllWindows()

    return count
