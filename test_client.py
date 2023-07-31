#! /usr/bin/python3

"""
A small test file use for testing the different class and function written in communication_module.py
"""

import communication_module as com


def TEST_initialisation_client(): 
    """
    testing both the constructer and __str__ of the class
    CommicationModuleClient
    """
    client = com.CommunicationModuleClient()
    print("\n\tclient : ")
    print(client)
    
    
def TEST_send_file():  
    """
    testing CommicationModuleClient
    """
    client = com.CommunicationModuleClient()
    print("\n\tsend of the file test : \n")  
    client.send_file("bigRandom_files/hugeRandom_file.txt")

def TEST_read_file():  
    """
    testing CommicationModuleClient
    """
    client = com.CommunicationModuleClient()
    print("\n\tget the file test : \n")  
    client.read_file("nouveau_fichier_test.txt")
    
    
TEST_read_file()