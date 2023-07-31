#! /usr/bin/python3

"""
A small test file use for testing the different class and function written in communication_module-SYM.py
"""

#! /usr/bin/python3

"""
A small test file use for testing the different class and function written in communication_module-SYM.py
"""

import communication_module_SYM as com

file_to_send = "hugeRandom_file.txt"
file_to_get = "nouveau_fichier_test.txt"
file_to_set_public = "nouveau_fichier_test.txt"


def TEST_initialisation():
    """
    testing both the constructer and __str__ of the class
    CommicationModuleClient
    """
    print("\n\tTEST initialisation is started : \n")
    aOrb = com.CommunicationModule()
    print("\n\tAlice or Bob example : ")
    print(aOrb)
    print("END of the test of initialisation")


def TEST_send_file():
    """
    testing CommicationModuleClient
    """
    print("\n\tTEST send_file is started : \n")
    aOrb = com.CommunicationModule()
    print("\n\tsend of the file test : \n")
    aOrb.send_file(file_to_send)
    print("END of the test of send_file")


def TEST_get_file():
    """
    testing CommicationModuleClient
    """
    print("\n\tTEST read_file is started : \n")
    aOrb = com.CommunicationModule()
    print("\n\tget the file test : \n")
    aOrb.get_file(file_to_get)
    print("END of the test of get_file")


def TEST_start_server():
    print("\n\tTEST start_server is started : \n")
    aOrb = com.CommunicationModule()
    aOrb.start_server()
    print("END of the test of start_server")
    
def TEST_authorized_file_access(): 
    print("\n\tTEST authorized_file_access is started : \n")
    aOrb = com.CommunicationModule()
    aOrb.authorized_file_access(file_to_set_public)
    print("END of the test of authorized_file_access")
    


TEST_start_server()
