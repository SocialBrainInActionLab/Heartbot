#!/usr/bin/env python
#
#	This is based on "miro_ros_client_lights" focuses
#	on controlling the on-board LED lights by conseuqential robotics
# 
#   It has been modified to change the pulse rate of the light 
#   flash
#

################################################################

import rospy
from std_msgs.msg import String#,Float32MultiArray,UInt16MultiArray
from std_msgs.msg import Float32MultiArray, UInt32MultiArray
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Twist

import math
import numpy as np
import time
import sys
import os
import miro2 as miro
from datetime import datetime

################################################################

def error(msg):
	print(msg)
	sys.exit(0)

def usage():
	print """
Usage:
	miro_ros_client_lights.py robot=<robot_name>

	Without arguments, this help page is displayed. To run the
	client you must specify at least the option "robot".

Options:
	robot=<robot_name>
		specify the name of the miro robot to connect to,
		which forms the ros base topic "/miro/<robot_name>".
		there is no default, this argument must be specified.
	"""
	sys.exit(0)

################################################################

class miro_ros_client_std:
	
	def __init__(self, robot_name, hr_reader=None, asynchMode=False, logger=None):
		
		# report
		print("initialising robot...")
		print(sys.version)
		
		self.heart_rate = 60.0/60.0    # 60 beats per second
		self.robot_name = robot_name
		self.hr_reader = hr_reader	
		
		self.asynchMode = asynchMode
		
        if self.asynchMode:
            self.heart_rate = self.heart_rate * 0.8 
        self.logger = logger
		
		# check we got at least one
		if len(self.robot_name) == 0:
			error("argument \"robot\" must be specified")
			
		self.set_active = False
			
		
		# topic root
		topic_root = "/" + self.robot_name + "/"
		#print "topic_root", topic_root
		
		# publish
		topic_name = topic_root + "control/illum" #"/platform/control/lights"
		if self.logger:
			self.logger.info("Publishing on: %s" % topic_name)
		self.pub_lights = rospy.Publisher(topic_name, UInt32MultiArray, queue_size=0)
		
		
		if self.logger:
			self.logger.info("Miro Initialised")
		
	def update_heart_rate(self):
		updated_rate = 1.0
		if self.hr_reader and not self.asynchMode:
			rate = self.hr_reader.heartRate
			updated_rate = float(rate)/60.0
			#
			if updated_rate > 0.01 and self.heart_rate != updated_rate:
				print("Updating robot rate to  %f bps" % updated_rate)
				self.heart_rate = updated_rate
				if self.logger:
					self.logger.info("Miro heart_rate updated to : %f beats per seond" % self.heart_rate)
		elif self.hr_reader and self.asynchMode:
            # a quarter rate for asynch
            rate = self.hr_reader.heartRate
            updated_rate = (float(rate) * 0.8)/60.0
            
            if updated_rate > 0.01 and self.heart_rate != updated_rate:
                print("Updating robot asynchronous rate to  %f bps" % updated_rate)
                self.heart_rate = updated_rate	
	            if self.logger:
					self.logger.info("Miro asynchronous heart_rate updated to : %f beats per seond" % self.heart_rate)
		 		
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
					   self.logger.info("Miro heart_rate updated to : %f beats per seond" % self.heart_rate)
	
	

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
		# color for six LEDs: [front_left, middle_left, back_left, front_right, etc.]
		rgb = [0x00FFFFFF, 0x00FFFFFF,  0x00FFFFFF, 0x00FFFFFF, 0x00FFFFFF,  0x00FFFFFF]
		try:
			# loop
			while self.set_active and not rospy.core.is_shutdown():
				
				# Get an update of heart rate from the reader
				self.update_heart_rate()
				
				# update pulse rate for the robot
				if self.logger:
					self.logger.info("Miro current heart_rate: %f beats per seond" % self.heart_rate)
				f_pulse = self.heart_rate/2.0
				
				# create message
				l = UInt32MultiArray()
				l.data = np.zeros([6], 'uint32')
				this_time = datetime.now()
				if last_time:
					phase_time = (this_time - last_time).total_seconds()
				# increment pulse phase by current rate
				phase += phase_time * f_pulse * 2 * np.pi
				last_time = this_time
	
				# magnitude
				mag = np.cos(phase) * 0.5 + 0.5
				bright = int(mag * 0xFF) << 24
	
				if self.logger:
					self.logger.info("Phase: %f \t Brightness: %f" %(np.degrees(phase), bright))
	
				
				# fix up the brightness
				for j in range(0, 6):
				     if rgb[j]:
				     	l.data[j] = rgb[j] | bright
	
				#print l
	
				# publish
				self.pub_lights.publish(l)
	
				# sleep
				time.sleep(T)
				
		finally:
			# Switch off the lights
			l = UInt32MultiArray()
			l.data = np.zeros([6], 'uint32')
			# publish
			self.pub_lights.publish(l)

def setup_heartbot(robot_name, hr_reader=None, logger=None):
	main_robot = miro_ros_client_std(robot_name, hr_reader, logger)
	rospy.init_node("miro_ros_client_std", anonymous=True)
	return main_robot
									
if __name__ == "__main__":
	main = setup_heartbot("miro")
	main.synch_hr()
	


