"""
This script creates a simple flask app so that the car can be manually controlled through a website for data collection to train CNN.
"""

from flask import Flask, render_template, Response
import RPi.GPIO as GPIO 
import cv2
import atexit  # <-- added

#Setting up the GPIO pins with their associated connections to the motor driver
ENA = 12 #Enable pin for left motor
#Direction controls for left motor
IN1 = 17 
IN2 = 27
#Direction controls for right motor
IN3 = 22
IN4 = 23
ENB = 13 #Enable pin for right motor

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [ENA, IN1, IN2, IN3, IN4, ENB]:
    GPIO.setup(pin, GPIO.OUT)

#PWM swithces motor voltage 1000 times per second
pwm_left = GPIO.PWM(ENA, 1000)
pwm_right = GPIO.PWM(ENB, 1000)

#Duty cycle = 0% -> motor doesn't spin
pwm_left.start(0)
pwm_right.start(0)

#Motors are not perfectly matched -> requires calibration
LEFT_CAL = 0.9
RIGHT_CAL = 0.7

# -- DIRECTION CONTROLS -- 
def forward(speed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    max_cal = max(LEFT_CAL, RIGHT_CAL)
    pwm_left.ChangeDutyCycle(speed*(LEFT_CAL/max_cal)) 
    pwm_right.ChangeDutyCycle(speed*(RIGHT_CAL/max_cal)) 

def backward(speed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    max_cal = max(LEFT_CAL, RIGHT_CAL)
    pwm_left.ChangeDutyCycle(speed*(LEFT_CAL/max_cal)) 
    pwm_right.ChangeDutyCycle(speed*(RIGHT_CAL/max_cal))  

def right(speed_left, speed_right):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    max_cal = max(LEFT_CAL, RIGHT_CAL)
    pwm_left.ChangeDutyCycle(speed_left*(LEFT_CAL/max_cal)) 
    pwm_right.ChangeDutyCycle(speed_right*(RIGHT_CAL/max_cal))

def left(speed_left, speed_right):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    max_cal = max(LEFT_CAL, RIGHT_CAL)
    pwm_left.ChangeDutyCycle(speed_left*(LEFT_CAL/max_cal)) 
    pwm_right.ChangeDutyCycle(speed_right*(RIGHT_CAL/max_cal))

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

#index.html set as control page
@app.route("/")
def index():
    return render_template("index.html")

#browser sends requests depending on direction selected by user
@app.route("/<cmd>")
def command(cmd):
    if cmd == "forward": forward(70)
    elif cmd == "backward": backward(70)
    elif cmd == "left": left(70,70)
    elif cmd == "right": right(70,70)
    elif cmd == "stop": stop()
    return "OK"

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

#Stream frames in real time
@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

#Run on all IPs and with port 5000
if __name__ == "__main__":
    app.run(host='0.0.0.0', port = 5000, threaded=True)  # <-- threaded added
