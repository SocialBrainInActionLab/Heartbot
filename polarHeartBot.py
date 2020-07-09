# Using Hexiwear with Python
import pexpect
import time
import logging
import sys
import os
import string
from exceptions import Exception

from datetime import datetime
from HR_reader import HeartBeat_BLE



MAX_CONN_RETRY = 5
MAX_NULL_HR = 10
WITH_ROBOT=True       # without robot to test the polar OH only
ROBOT_TYPE = "Miro"   # Set this to Pepper or Miro

if WITH_ROBOT and ROBOT_TYPE=="Miro":
    from miro_heartbot_lights import setup_heartbot
elif WITH_ROBOT and ROBOT_TYPE=="Pepper":
    from pepper_heartbot_lights import PepperHandler

def add_logger(log_path, participantNumber):
    
    logger = logging.getLogger("HeartBot")
    logger.setLevel(logging.INFO)
    filename = "HeartBot_%s.log" % (datetime.now().strftime("%H%M%S_%d%m%Y"))
    filePath = os.path.join(log_path, filename)
    
    # create error file handler and set level to info
    handler = logging.FileHandler(os.path.join(log_path, filename),"w", encoding=None, delay="true")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger



def main(doAsynch, logger):
    max_retry = MAX_CONN_RETRY
    do_relay = False
    hr_polarOH = None
    heart_robot = None
    try: 
        # Run gatttool interactively.
        hr_polarOH = HeartBeat_BLE(logger)
        if WITH_ROBOT:
            if ROBOT_TYPE == "Pepper":
                heart_robot = PepperHandler.getInstance(hr_polarOH, doAsynch, logger)
            elif ROBOT_TYPE == "Miro":
                heart_robot = setup_heartbot("miro", hr_polarOH, doAsynch, logger)
            else: 
                raise Exception("Do not recognize robot: %s" % ROBOT_TYPE)
        
        #-------------------------------------------------------
        # Setting up connection
        while max_retry >= 0:
            try:
                # try connecting to the heart-rate tool
                index = hr_polarOH.connect()
                if index > 0:
                    #connection was successful 
                    hr_polarOH.switch_HR_notifications(True)
                    hr_polarOH.start()
                    do_relay = True
                    break
            except pexpect.TIMEOUT:
                pass
            
            logger.info("Startup connection failure")
            # some issue let's retry
            if max_retry > 0:
                print("Connection failed. Will retry %d more times" % max_retry)
                max_retry -= 1
                
                # send peripheral a disconnect signal and sleep and retry
                hr_polarOH.disconnect()
                time.sleep(0.5)
               
            else:
                # No more tryies left 
                max_retry -= 1
                print("Connection failed. Please restart bluetooth on measurement tool")
        #------------------------------------------------------
        # Now for robot to read the heart_rate
        max_retry = MAX_NULL_HR
        if do_relay:
            print("Starting heart-beat relay")
            logger.info("Starting heart-beat relay")
            if heart_robot:
                print("Starting heart-beat relay with robot")
                heart_robot.synch_hr()
            else:
                for i in range(10):
                    print hr_polarOH.heartRate
                    time.sleep(2)
            
    
    finally:   
    	print("Closing connection to heart-rate tool")
    	logger.info("Closing connection to heart-rate tool")
    	if hr_polarOH:
    	    hr_polarOH.stop() 
            
        if heart_robot:
            heart_robot.set_active=False
                
        
if __name__ =='__main__':
    if len(sys.argv) < 2:
        print("Please make sure you have provided the participant number")
    else:
        asynchMode = False
        participantNumber = int(sys.argv[1])
        if len(sys.argv) == 3:
            if string.lower(sys.argv[2]) == "async":
                asynchMode = True
        log_path = './Logs'
        log_path = os.path.join(log_path, 'P%d' % participantNumber)
        if not os.path.isdir(log_path):
            os.mkdir(log_path)
        logger = add_logger(log_path, None)
        logger.info("Participant Number %d" % participantNumber)
        main(asynchMode, logger)
    

    
