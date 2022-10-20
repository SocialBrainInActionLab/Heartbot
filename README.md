# Heartbot

[![DOI](https://zenodo.org/badge/278386987.svg)](https://zenodo.org/badge/latestdoi/278386987)

This code attempts to synchronize user heartbeat rate to robot light pulse. You can select between two robots to run the HeartBot with - Pepper a humanoid robot (from Aldebaran) and Miro-e an animal-like robot(by Consequential robotics). The heartbeat is measure using a PolarOH heart rate monitor. PolarOH uses Bluetooth LE(BLE) to communicate with the computer. Both the afore mentioned robot (and its lights) allows interface through python programming. But for python to interface to the BLE 'gattool' is required. However Windows OS (up to windows 10) does not run gattool as expected. So a unix based system needs to be used. This can be done using a VirtualBox or a VirtualMachine. However the Miro robot does not work well with either VirtualBox or VirtualMachine and needs Ubuntu 16.04 LTS. Consequential robotics recommended a system running on Ubuntu (or atleast a dual boot with Ubuntu). So for this we recommnd a Ubuntu OS(not vitual OS) as well.

The code can be run in synchronous and asynchronous mode. In synchronous mode the heatbeat rate matches the light pulsing rate. And in asynchronous mode the robot light pulses at 80% of user heart rate.

## To run heartbot

python polarHeartBot.py *participant-number* [async]

The participant parameter is required for logging
If the 'async' parameter is provided then the system runs in asynchronous mode. Its absence indicates synchronous mode.

To switch between robots change the value of the polarHeartBot.py > ROBOT_TYPE  to Miro or Pepper.

For running with Pepper the naoqi sdk for python needs to be installed on the ubuntu system as recommended by Aldebaran.

For running with Miro the miro app the rospy interface needs to be setup as recommended by Consequential robotics. Once that is done, the Miro app needs to be used to switch off "Emoting with lights" before running the python programme. If Miro needs to be running in demo mode, this has to be done through the Miro app.
