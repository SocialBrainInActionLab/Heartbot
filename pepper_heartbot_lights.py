import math
import numpy as np
import os
import time
import sys
from datetime import datetime

from naoqi import ALProxy


ROBOT_IP = '192.168.1.193'
#ROBOT_IP = '192.168.1.163'
#ROBOT_IP = '192.168.1.162'


class PepperHandler(object):
    __instance = None
    
    @staticmethod 
    def getInstance(hr_reader=None, asynchMode=False, logger=None):
       """ Static access method. To create singleton handler """
       if PepperHandler.__instance == None:
          # Create new
          PepperHandler(hr_reader, asynchMode, logger)
          
       return PepperHandler.__instance
          
    
    def __init__(self, hr_reader, asynchMode, logger):
        
        if PepperHandler.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            PepperHandler.__instance = self
            super(PepperHandler, self).__init__()
            self.motion_handler = ALProxy("ALMotion", ROBOT_IP, 9559)
            self.motion_handler.wakeUp()
            self.basic_awareness = ALProxy("ALBasicAwareness", ROBOT_IP, 9559)
            self.basic_awareness.stopAwareness()
            self.motion_handler.setBreathConfig([['Bpm', 2.0], ['Amplitude', 1.0]])
            self.motion_handler.setBreathEnabled ('Body', False)
            self.motion_handler.setBreathEnabled ('Arms', True)
            self.headLockPitch = None
            self.headLockYaw = None
            
            self.heart_rate = 60.0/60.0    # 60 beats per second
            self.hr_reader = hr_reader 
            self.asynchMode = asynchMode
            if self.asynchMode:
                self.heart_rate = self.heart_rate * 0.8 
            
            self.logger = logger
            # The Leds we want to use for heart beat display            
            # Create a new group
            heart_led_group = [# Ear Led
                                "Ears/Led/Right/0Deg/Actuator/Value",
                                "Ears/Led/Left/0Deg/Actuator/Value",
                                "Ears/Led/Right/36Deg/Actuator/Value",
                                "Ears/Led/Left/36Deg/Actuator/Value",
                                "Ears/Led/Right/72Deg/Actuator/Value",
                                "Ears/Led/Left/72Deg/Actuator/Value",
                                "Ears/Led/Right/108Deg/Actuator/Value",
                                "Ears/Led/Left/108Deg/Actuator/Value",
                                "Ears/Led/Right/144Deg/Actuator/Value",
                                "Ears/Led/Left/144Deg/Actuator/Value",
                                "Ears/Led/Right/180Deg/Actuator/Value",
                                "Ears/Led/Left/180Deg/Actuator/Value",
                                "Ears/Led/Right/216Deg/Actuator/Value",
                                "Ears/Led/Left/216Deg/Actuator/Value",
                                "Ears/Led/Right/252Deg/Actuator/Value",
                                "Ears/Led/Left/252Deg/Actuator/Value",
                                "Ears/Led/Right/288Deg/Actuator/Value",
                                "Ears/Led/Left/288Deg/Actuator/Value",
                                "Ears/Led/Right/324Deg/Actuator/Value",
                                "Ears/Led/Left/324Deg/Actuator/Value",
                                #Shoulder Leds
                                "ChestBoard/Led/Blue/Actuator/Value",
                                #"ChestBoard/Led/Green/Actuator/Value",
                                #"ChestBoard/Led/Red/Actuator/Value"
                                ]
            shoulder_led_group = [#Shoulder Leds
                                  "ChestBoard/Led/Blue/Actuator/Value",
                                  "ChestBoard/Led/Green/Actuator/Value",
                                  "ChestBoard/Led/Red/Actuator/Value"
                                ]
            
            self.leds = ALProxy("ALLeds",ROBOT_IP, 9559)
            self.leds.createGroup("HeartLeds",heart_led_group)
            self.leds.createGroup("ShoulderLeds",shoulder_led_group)
            # Switch the new group on
            self.leds.off("ShoulderLeds")
            self.leds.on("HeartLeds")
            
    def update_heart_rate(self):
        if self.hr_reader and not self.asynchMode:
            rate = self.hr_reader.heartRate
            updated_rate = float(rate)/60.0
            #
            if updated_rate > 0.01 and self.heart_rate != updated_rate:
                print("Updating robot rate to  %f bps" % updated_rate)
                self.heart_rate = updated_rate
                if self.logger:
                    self.logger.info("Pepper heart_rate updated to : %f beats per second" % self.heart_rate)
        elif self.hr_reader and self.asynchMode:
            # a quarter rate for asynch
            rate = self.hr_reader.heartRate
            updated_rate = (float(rate) * 0.8)/60.0
            
            if updated_rate > 0.01 and self.heart_rate != updated_rate:
                print("Updating robot asynchronous rate to  %f bps" % updated_rate)
                self.heart_rate = updated_rate
                if self.logger:
                    self.logger.info("Pepper asynchronous heart_rate updated to : %f beats per second" % self.heart_rate)
        else:
            # Read from file
            hr_file = "./heartRate.txt"
            if os.path.isfile(hr_file):
                if self.logger:
                    self.logger.info("Updating heart_rate from file")
                f = hr_file.open()
                rate = int(f.readline())
                updated_rate = float(rate)/60.0
                if updated_rate > 0.01 and self.heart_rate != updated_rate:
                    print("Updating robot rate to  %f bps" % updated_rate)
                    self.heart_rate = updated_rate
                    if self.logger:
                       self.logger.info("Pepper heart_rate updated to : %f beats per second" % self.heart_rate)
    
    
        

    def synch_hr(self):
        
        # wait for connection
        # "waiting for subscribers..."
        time.sleep(1)
        self.set_active = True

        # params
        T = .05 # update time
        phase = 0.0 
        phase_time = T
        last_time = None
        
        try:
            # loop
            while self.set_active:
                
                # Get an update of heart rate from the reader
                self.update_heart_rate()
                
                # update pulse rate for the robot
                if self.logger:
                    self.logger.info("Pepper current heart_rate: %f beats per seond" % self.heart_rate)
                f_pulse = self.heart_rate/2.0
                
                # calculate intesity phase
                this_time = datetime.now()
                if last_time:
                    phase_time = (this_time - last_time).total_seconds()
                # increment pulse phase by current rate
                phase += phase_time * f_pulse * 2 * np.pi
                last_time = this_time
    
                # magnitude
                mag = np.cos(phase) * 0.5 + 0.5
                
                if self.logger:
                    self.logger.info("Phase: %f \t Brightness: %f" %(np.degrees(phase), mag))
    
                
                # fix up the brightness
                self.leds.setIntensity("HeartLeds", mag)
    
                # sleep
                time.sleep(T)
                
        finally:
            # Switch off the lights
            self.leds.off("HeartLeds")


if __name__ =='__main__':
    main_robot = PepperHandler.getInstance(hr_reader=None, logger=None)
    main_robot.synch_hr()
                        