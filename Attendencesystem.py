import face_recognition
import cv2
import numpy as np
import datetime
import openpyxl
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from twilio.rest import Client

# Load configuration from a JSON file
with open('config.json') as config_file:
    config = json.load(config_file)

# Twilio configuration
account_sid = "your_twilio account sid"
auth_token = "authentic_token"
twilio_phone_number = 'number'

# Initialize Twilio client
client = Client(account_sid, auth_token)

# Get a reference to webcam #0 (the default one)
video_capture = cv2.VideoCapture(0)

# Create arrays of known face encodings and their names
known_face_encodings = []
known_face_names = []
parent_numbers = {}

for person in config['people']:
    image = face_recognition.load_image_file(person['image_path'])
    face_encoding = face_recognition.face_encodings(image)[0]
    known_face_encodings.append(face_encoding)
    known_face_names.append(person['name'])
    parent_numbers[person['name']] = person['parent_number']

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
face_confidences = []  # Added: List to store confidence percentages
present_names = set()  # Added: Set to store names already marked as present
absent_names = set(known_face_names)  # Added: Set to store absent names initially
on_duty_names = set(config['on_duty_students'])  # Added: Set to store names of on-duty students

# Create an Excel workbook and worksheet
workbook = openpyxl.Workbook()
worksheet = workbook.active
worksheet["A1"] = "Name"
worksheet["B1"] = "Timestamp"
worksheet["C1"] = "Status"  # Added: Column to mark status (e.g., Present, OD)
row = 2

while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Only process every other frame of video to save time
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    face_names = []
    face_confidences = []  # Added: List to store confidence percentages

    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"
        confidence = 0  # Added: Initialize confidence to 0

        # Or instead, use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)

        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            confidence = (1 - face_distances[best_match_index]) * 100
            if name in absent_names and name not in present_names and confidence > 60:
                present_names.add(name)  # Add name to set of present names
                worksheet[f"A{row}"] = name
                if name in on_duty_names:
                    worksheet[f"B{row}"] = "OD"  # Mark on-duty students as "OD"
                    worksheet[f"C{row}"] = "Present"  # Mark status as "Present" for on-duty students
                else:
                    worksheet[f"B{row}"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    worksheet[f"C{row}"] = "Present"  # Mark status as "Present" for regular students
                row += 1

        face_names.append(name)
        face_confidences.append(confidence)

    # Mark on-duty students as "OD" if their faces are not recognized
    for name in on_duty_names:
        if name not in face_names and name not in present_names:
            present_names.add(name)  # Add name to set of present names
            worksheet[f"A{row}"] = name
            worksheet[f"B{row}"] = "OD"  # Mark on-duty students as "OD"
            worksheet[f"C{row}"] = "Present"  # Mark status as "Present" for on-duty students
            row += 1

    # Display the results
    for (top, right, bottom, left), name, confidence in zip(face_locations, face_names, face_confidences):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Check if confidence is above 50%
        if confidence > 50:
            color = (0, 255, 0)  # Green color for confidence > 50
            attendance_status = "Present"
        else:
            color = (0, 0, 255)  # Red color for confidence <= 50
            attendance_status = "Absent"

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        # Draw a label with a name and confidence below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, f"{name}: {confidence:.2f}%", (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

# Save the Excel workbook
absent_names_list = list(absent_names - present_names)  # Exclude names already marked as present  
for name in absent_names_list:
    worksheet[f"A{row}"] = name
    worksheet[f"B{row}"] = "Absent"
    worksheet[f"C{row}"] = "Absent"  # Mark status as "Absent" for absent students
    row += 1
workbook.save("attendance.xlsx")
print("Attendance Successful")

# Send SMS notifications to parents of absent students
for name in absent_names_list:
    parent_number = parent_numbers.get(name)
    if parent_number:
        message = f"Your child, {name}, is absent today."
        client.messages.create(body=message, from_=twilio_phone_number, to=parent_number)

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()
























import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(sender_email, sender_password, receiver_email, subject, body, attachment_path):
    # Create a multipart message object and set the sender, receiver, subject, and body
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Open the file in bytestream mode
    with open(attachment_path, "rb") as attachment:
        # Add file as application/octet-stream
        # Email clients can usually download this automatically as an attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode the file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add a header to tell the email client the name of the attached file
    part.add_header("Content-Disposition", "attachment", filename=attachment_path)

    # Add the attachment to the message and convert it to a string
    message.attach(part)
    text = message.as_string()

    # Connect to the SMTP server, send the email, and close the connection
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, text)

# Example usage
sender_email = "sender mail"
sender_password = "sender password"
receiver_email = "receiver mail"
subject = "Attendance Report"
body = "ATTENDANCE REPORT"
attachment_path = os.path.join("attendance.xlsx")
send_email(sender_email, sender_password, receiver_email, subject, body, attachment_path)
print("Email sent successfully")
