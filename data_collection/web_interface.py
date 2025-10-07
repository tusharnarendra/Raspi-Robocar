"""
This script creates a simple flask app so that the car can be manually controlled through a website for data collection to train CNN.
"""

from flask import Flask, render_template, Response
import RPi.GPIO as GPIO 
import cv2
import atexit  
import os
import csv
from datetime import datetime
import threading
import time


# -- DATASET SETUP --

#Creating directories to store dataset
dataset_dir = "dataset"
images_dir = os.path.join(dataset_dir, "images")

# Define possible labels (old system )
#labels = ["forward", "backward", "left", "right", "stop"]
# Create subfolders for each label
#for label in labels:
    #os.makedirs(os.path.join(images_dir, label), exist_ok=True)

#Determing which direction has most available space
space_labels = {
    'w': 'space_forward',
    'a': 'space_left',
    'd': 'space_right',
    's': 'stop'
}

for folder in space_labels.values():
    os.makedirs(os.path.join(images_dir, folder), exist_ok=True)
    
#Function to save image and label
def save_frame(frame, label):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}.jpg"
    path = os.path.join(images_dir, label, filename)
    cv2.imwrite(path, frame)

#Setting up the GPIO pins with their associated connections to the motor driver
ENA = 12 #Enable pin for right motor
#Direction controls for right motor
IN1 = 17 
IN2 = 27
#Direction controls for left motor
IN3 = 22
IN4 = 23
ENB = 13 #Enable pin for left motor

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [ENA, IN1, IN2, IN3, IN4, ENB]:
    GPIO.setup(pin, GPIO.OUT)

#PWM swithces motor voltage 1000 times per second
pwm_left = GPIO.PWM(ENB, 1000)
pwm_right = GPIO.PWM(ENA, 1000)

#Duty cycle = 0% -> motor doesn't spin
pwm_left.start(0)
pwm_right.start(0)

#Motors are not perfectly matched -> requires calibration
RIGHT_CAL = 0.65
LEFT_CAL = 0.725

# -- DIRECTION CONTROLS -- 
def forward(speed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed*(LEFT_CAL)) 
    pwm_right.ChangeDutyCycle(speed*(RIGHT_CAL)) 

def backward(speed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed*(LEFT_CAL)) 
    pwm_right.ChangeDutyCycle(speed*(RIGHT_CAL))  

def right(speed):
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed * LEFT_CAL)

    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    pwm_right.ChangeDutyCycle(0)

def left(speed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm_right.ChangeDutyCycle(speed * RIGHT_CAL)

    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(0)

def stop():
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)

# -- Cleanup on exit --
def cleanup():
    stop()
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()

atexit.register(cleanup)

# -- FLASK APP --

app = Flask(__name__)

camera = cv2.VideoCapture(0)

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#index.html set as control page
@app.route("/")
def index():
    return render_template("index.html")


#browser sends requests depending on direction selected by user
@app.route("/<cmd>")
def command(cmd):
    if cmd == "forward_arrow": forward(60)
    elif cmd == "backward_arrow": backward(60)
    elif cmd == "left_arrow": left(50)
    elif cmd == "right_arrow": right(50)
    elif cmd == "stop": stop()
    elif cmd in ["w", "a", "d", "s"]:
        success, frame = camera.read()
        if success:
            label_map = {"w": "space_forward", "a": "space_left", "d": "space_right", "s": "stop"}
            save_frame(frame, label_map[cmd])
    return "OK"


#Stream frames in real time
@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')


#Run on all IPs and with port 5000
if __name__ == "__main__":
    app.run(host='0.0.0.0', port = 5000, threaded=True)  # <-- threaded added
