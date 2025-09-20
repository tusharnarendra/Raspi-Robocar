import RPi.GPIO as GPIO
import time

ENA = 12
IN1 = 17
IN2 = 27
IN3 = 22
IN4 = 23
ENB = 13

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [ENA, IN1, IN2, IN3, IN4, ENB]:
    GPIO.setup(pin, GPIO.OUT)

pwm_left = GPIO.PWM(ENA, 1000)
pwm_right = GPIO.PWM(ENB, 1000)

pwm_left.start(0)
pwm_right.start(0)

def forward():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(90) 
    pwm_right.ChangeDutyCycle(70)

def stop():
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)

try:
    print("Moving forward for 2 seconds... ")
    forward()
    time.sleep(2)
    stop()
    print("Stopped")
finally:
    # Clean shutdown
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()
    del pwm_left
    del pwm_right