#! /usr/bin/python3

"""
A small test file use for testing the different method of the server written in communication_module.py
"""

import communication_module as com
import os


def TEST_initialisation_server(): 
    """
    testing the constructer and and the methods stop and start_server
    of the class CommicationModuleServer
    """
    srv = com.CommunicationModuleServer()
    print("\n\tsrv : ")
    print(srv)
    print("\nTest if we can launch the server : ")
    srv.start_server()
    print(f"server on : {srv.server_on}")
    os.system("ps aux | grep sshd")
    print("\nTest if we can stop the server : ")
    srv.stop_server()
    print(f"server off : {not srv.server_on}")
    os.system("ps aux | grep sshd")
    
    
def TEST_send_file():  
    """
    testing CommicationModuleClient
    """
    client = com.CommunicationModuleClient()
    print("send of the file test : ")  
    client.send_file("sendMe_to_Bob.txt")
    print('OK!')

def TEST_read_file():  
    """
    testing CommicationModuleClient
    """
    client = com.CommunicationModuleClient()
    print("get the file test : ")  
    client.read_file("test_text.txt")
    print('OK!')
    
    

