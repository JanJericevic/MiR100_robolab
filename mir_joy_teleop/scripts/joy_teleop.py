#!/usr/bin/env python

""" ROS joystick teleoperation script. Optional REST API interaction for MiR 100 robot. 

Requirements:
To get joystick data, ROS joy_node is needed (http://wiki.ros.org/joy). 
To interact with the robot's REST API, the script uses imported MirRestApi class from the mir_rest_api ROS package.

Instructions:
Customize button configuration accordingly.
Used button configuration for Logitech F710 joystick.

left stick vertical axis: linear speed
right stick horizontal axis: angular speed

left bumper: increase stick linear speed range
left trigger: decrease stick linear speed range
right bumper: increase stick angular speed range
right trigger: decrease stick angular speed range

MiR 100 REST API interactions:
x: toggle robot state - Ready/Pause. Used to start/stop execution of mission queue
a: retrieve current robot mode
b: delete mission queue
y: retrieve current robot status
"""

import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy
from mir_rest_api.api import MirRestApi
from pprint import pprint

class JoyTeleop:
    """Joystick teleop class

    :param api: class used for MiR 100 REST API communication, defaults to None
    :type api: MirRestApi, optional
    """

    def __init__(self, api: MirRestApi=None) -> None:
        self.vel = Twist()
        self.range_lin_speed = 0.4
        self.range_ang_speed = 0.3
        self.min_lin_speed = 0.1
        self.min_ang_speed = 0.1
        self.max_lin_speed = 2.0
        self.max_ang_speed = 1.0

        self.api = api

        self.pub = rospy.Publisher('cmd_vel', Twist, queue_size=1)
        self.sub = rospy.Subscriber("joy", Joy, self.read_joy)

    def read_joy(self, data: Joy) -> None:
        """Handles joystick data

        :param data: ROS joystick data
        :type data: Joy
        """
        self.vel.linear.x = self.range_lin_speed*data.axes[1]
        self.vel.angular.z = self.range_ang_speed*data.axes[2]
       
        # adjust speed ranges
        # TODO: simultaneous stick and button data bug
        if (data.buttons[4] == 1) and (self.range_lin_speed < self.max_lin_speed):
            self.range_lin_speed = self.range_lin_speed + 0.1
            rospy.loginfo("MAX LIN SPEED = %s", self.range_lin_speed)

        elif (data.buttons[6] == 1) and (self.range_lin_speed > self.min_lin_speed):
            self.range_lin_speed = self.range_lin_speed - 0.1
            rospy.loginfo("MAX LIN SPEED = %s", self.range_lin_speed)

        elif (data.buttons[5] == 1) and (self.range_ang_speed < self.max_ang_speed):
            self.range_ang_speed = self.range_ang_speed + 0.1
            rospy.loginfo("MAX ANG SPEED = %s", self.range_ang_speed)

        elif (data.buttons[7] == 1) and (self.range_ang_speed > self.min_ang_speed):
            self.range_ang_speed = self.range_ang_speed - 0.1
            rospy.loginfo("MAX ANG SPEED = %s", self.range_ang_speed)

        # using joystick & MiR100 robot REST API
        if data.buttons[0] == 1:
            response = self.api.status_state_id_toggle_put(False)
            pprint(response)
        if data.buttons[1] == 1:
            response = self.api.status_mode_get(False)
            pprint(response)
        if data.buttons[2] == 1:
            response = self.api.mission_queue_delete(False)
            pprint(response)
        if data.buttons[3] == 1:
            response = self.api.status_get(False)
            pprint(response)
        
    def publish(self, event=None):
        """Publishes velocity values to 'cmd_vel' topic

        :param event: _description_, defaults to None
        :type event: _type_, optional
        """
        self.pub.publish(self.vel)

def main(): 
    # set the MiR100 ip
    ip = "193.2.178.59"

    # if using ROS service for REST requests
    # rospy.wait_for_service('mir_rest_api_service')

    api = MirRestApi("UserName", "Password", ip)   
    rospy.init_node('joy_teleop_node', anonymous=True)
    jt = JoyTeleop(api)
    
    rospy.Timer(rospy.Duration(1.0/50.0), jt.publish)

    rospy.spin()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass