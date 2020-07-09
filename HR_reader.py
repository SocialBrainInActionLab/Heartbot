# Hear beat reader synchronised to a specific device whose mac address has been
# hardcoded in. 
# This device is a polarOH heart rate reader. It broadcasts the heartrate notification
# when the notifications are switched on.
# Unlike some other device(e.g. Hexiwear) which just broadcasts all values of interest at 
# all time this needs to be switched on for each value of interest
import pexpect
import threading
import time
DEVICE = 'A0:9E:1A:25:71:5C'     # Mac address of the device

class HeartBeat_BLE(threading.Thread):
    
    def __init__(self, logger=None):
        """
        Initialise the gattool. Note we need to be on a Unix based system
        @param logger: If logging is required then a python logger needs to be passed to it 
        """
        # This implements threading so super class thread will need initialising
        super(self.__class__, self).__init__()
        print("Run gatttool...")
        
        # The gattHandle is the pipe to the gatttool which speaks to the device
        self.gattHandle = pexpect.spawn("gatttool -I")    
        self.stop_thread = False
        self.listen = False
        self.heartRate = 60      # This value is updated with new measured heart rate
        self.logger = logger
        
        
        
    def hexStrToInt(self, hexstr):
        """
        Function to transform hexadecimal string like "cd" i.e.0xCD into signed integer
        """
        val = int(hexstr[4],16) + (int(hexstr[3],16)<<4)
        return val
    
    def stop(self):
        """
        Cleaning up and stopping thread
        """
        self.stop_thread = True
        time.sleep(0.5)
        # switch of notifications since we will no longer be listening to them
        self.switch_HR_notifications(False)
        # Close the gatthandle
        self.gattHandle.close(force=True)
        self.gattHandle = None
        self.heartRate = -1
        

    def connect(self):
        """
        Attempts to connect to the BLE measurement tool via the gattTool. The device needs to be connected to
        before starting the thread
        @return index: This value is 1 when there is a successful connection.
        """
        child = self.gattHandle
        index = -1
        # Connect to the device.
        print("Connecting to "),
        print(DEVICE),
        if self.logger:
            self.logger.info("Trying to connect to %s" %DEVICE)
        child.sendline("connect {0}".format(DEVICE))
        try:
            # Look out for success or error in connection
            index = child.expect(["connect error", "Connection successful"], timeout=10)
            if index > 0:
                print(" Connected!")
                if self.logger:
                    self.logger.info("Connected to %s" %DEVICE)
            else:
                print("Error connecting")
                if self.logger:
                    self.logger.info("Error Connecting to %s" %DEVICE)
        except pexpect.TIMEOUT:
            print("Timed out, device not responding to connection request. Please check device")
            if self.logger:
                self.logger.info("Timed out, device not responding to connection request. Please check device")
        
        return index
    
    def disconnect(self):
        """
        Attempts to disconnect from the BLE measurement tool. BLE devices can only be connected
        to one other device at a time. So it must be disconnected 
        """
        child = self.gattHandle
        child.sendline("disconnect {0}".format(DEVICE))
        # As long as we have sent the command out we are not too fussy about what device sends back
        # it may already have disconnected
        index = child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=5)
        return index 
    
    def switch_HR_notifications(self, switchOn=True):
        """
        Switching heart rate notification on/off
        @param switchOn: bool to indicated whether notification should be on
        """
        child = self.gattHandle
        if switchOn:
            # polarOH specific heart rate notification switch on command
            child.sendline("char-write-req 0x0026 0100")
        else:
            # polarOH specific heart rate notification switch off command
            child.sendline("char-write-req 0x0026 0000")
        # As long as it was written successfully we should have hear-rate brodcasting
        # switched on/off as needed
        child.expect("Characteristic value was written successfully", timeout=10)
        self.listen = switchOn
        
    def monitor_hr_notification(self):
        """
        Monitors heart-rate if the notification was switched on
        """
        child = self.gattHandle     
        # If notifications are on      
        if self.listen:
            # Listen for heart rate notification channel for values
            child.expect("Notification handle = 0x0025 value: ", timeout=30)
            child.expect("\r\n", timeout=30)
            
            # isolate the part that gives the heart rate value
            hr_string = child.before.strip()
            
            # hear rate values come in as hexadecimal strings reversed so
            # convert it to int
            hr = self.hexStrToInt(hr_string)
            if not self.heartRate == hr:
                #Log and update if there is a change of heart rate
                if self.logger:
                    self.logger.info("Heart rate change: %d to %d" % (self.heartRate, hr))
                self.heartRate = hr
            else:
                # print current heart rate 
                # print("Heart rate read: %s" % hr)
                if self.logger:
                    self.logger.info("Heart rate read: %d" % hr)
            
            
            
    def run(self):
        """
        Thread to constant monitor heart rate
        Some times device disconnects. We will retry connecting in that case
        But some reasonable number of times just in case the monitor has died
        i.e. signal to weak, not picking up, battery dead.
        """ 
        max_retry = 11 
        while not self.stop_thread:
            try:
                # read monitor
                self.monitor_hr_notification()    
                # reset retries
                max_retry = 11
            except pexpect.TIMEOUT:
                if self.stop_thread:
                    #We are to stop so do nothing
                    break
                if max_retry <= 1:
                    print("Heart rate monitor not responding... ")
                    if self.logger:
                        self.logger.info("Heart rate monitor not responding... ")
                    self.stop()
                else:
                    try:
                        max_retry -= 1
                        print("Heart rate notification error. Retry %d times" % max_retry)
                        if self.logger:
                            self.logger.info("Heart rate notification error. Retry %d times" % max_retry)
                        self.connect()
                        self.switch_HR_notifications(True)
                    except pexpect.TIMEOUT:
                        pass
            except Exception:
                # We are getting some errors when stopping the thread which we don't care about
                # if we are stopping
                if self.stop_thread:
                    #We are to stop so do nothing
                    break
                else:
                    raise
                
    
if __name__ =='__main__':
    hr_listener = None
    try:
        hr_listener = HeartBeat_BLE()
        hr_listener.connect()
        hr_listener.switch_HR_notifications(True)
        hr_listener.start()
        time.sleep(120)

    finally:
        print(" final stop")
        if hr_listener:
            hr_listener.stop()
    
    
    
    
