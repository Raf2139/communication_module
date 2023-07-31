#! /usr/bin/python3

"""
This file gonna define the class "CommunicationModule" that gonna be use for alice en bob 
communication.
"""


import pexpect  # To lanch a process and deal with it (better than "subprocess" for SFTP comand line interaction)
import yaml  # To importe and deal with the .yaml that we will use as config file
import subprocess
import time  # For make the deamons sleep
import sys
import os  # For searching if a file or a directory exit

# Import 'watchdog'. For the server monitoring
# of the files uploading by the client
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class CommunicationModule:
    def __init__(self, config_file="./config_SYM.yaml"):
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        """General attributes"""
        self.local_data_dir = config["local_data_dir"]
        self.server_ip = config["server_ip"]

        """attributes relative to SERVER part"""
        self.srv_ssh_exec = config[
            "srv_ssh_exec"
        ]  # path to the ssh server executable (sshd)
        self.srv_config_file = config["srv_config_file"]
        self.local_client_upload_dir = config["local_client_upload_dir"]
        self.local_srv_upload_dir = config["local_srv_upload_dir"]
        self.srv_on = False
        self.time_to_live = config["time_to_live"]

        """attributes relative to CLIENT part"""
        self.client_ssh_exec = config[
            "client_ssh_exec"
        ]  # path to the ssh client executable
        self.client_config_file = config["client_config_file"]
        self.remote_client_upload_dir = config["remote_client_upload_dir"]
        self.remote_srv_upload_dir = config["remote_srv_upload_dir"]
        self.username = config["username"]

    def __str__(self):
        """
        We defined the __str__ methods because we gonna
        use it for debugging.
        """
        string_to_return = (
            "\tGeneral : \n"
            f"local_data_dir : {self.local_data_dir}\n"
            f"server_ip : {self.server_ip}\n"
            "\n\tServer : \n"
            f"srv_ssh_exec : {self.srv_ssh_exec}\n"
            f"srv_config_file : {self.srv_config_file}\n"
            f"local_client_upload_dir : {self.local_client_upload_dir}\n"
            f"local_srv_upload_dir : {self.local_srv_upload_dir}\n"
            f"srv_on : {self.srv_on}\n"
            f"time_to_live : {self.time_to_live}\n"
            "\n\tClient : \n"
            f"client_ssh_exec : {self.client_ssh_exec}\n"
            f"client_config_file : {self.client_config_file}\n"
            f"remote_client_upload_dir : {self.remote_client_upload_dir}\n"
            f"remote_srv_upload_dir : {self.remote_srv_upload_dir}\n"
            f"username : {self.username}\n"
        )
        return string_to_return

    ##################################SERVER#################################

    def client_upload_monitoring_deamon(self):
        """
        TODO : finish to right properly this part and add it to the methodes
        start_server
        """
        my_event_handler = MyEventHandler(self)
        my_observer = Observer()
        my_observer.schedule(
            event_handler=my_event_handler,
            path=self.local_client_upload_dir,
            recursive=True,
        )
        my_observer.start()
        living_time = 0
        while living_time < self.time_to_live:
            time.sleep(1)
            living_time += 1
        my_observer.stop()
        my_observer.join()

    def stop_server(self):
        print("We stoped the oqs-ssh server")
        ssh_pid = (
            (
                subprocess.run(
                    ["cat", "/var/run/sshd.pid"],
                    capture_output=True,
                    check=True,
                )
            )
            .stdout[0:-1]
            .decode()
        )
        if self.server_on:
            subprocess.run(["sudo", "kill", f"{ssh_pid}"], check=True)
            self.server_on = False

    def start_server(self, option=""):
        """
        TODO : include client_upload_monitoring_deamon in it and also
        add a TTL and call the function stop_server once the TTL is reach

        Start the server daemon using sshd and the different
        options pass as argument.
        """
        print("We starte the oqs-ssh server")
        print(f"IP : {get_IP()}")

        # Execute the sshd deamon as superuser
        process = subprocess.Popen(
            [
                "sudo",
                "bash",
                "-c",
                f"{self.srv_ssh_exec}",
                "-f",
                f"{self.srv_config_file}",
                option,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # start the watchdog on the directory of upload of the client
        self.client_upload_monitoring_deamon()

        # wait for the command to end (if the command is not finish in 10 sec an Error is raised)
        stdout, stderr = process.communicate(timeout=10)

        if process.returncode == 0:
            print(stdout.decode())
            self.server_on = True

        else:
            # print the standart and error output
            print(
                "Error while launching the server deamon : ",
                stderr.decode(),
                file=sys.stderr,
            )
            exit()

        # stop the server once the ttl is reach.
        self.stop_server()

    def authorized_file_access(self, file_name):
        if not os.path.exists(f"{self.local_data_dir}{file_name}"):
            print(
                f"The local file '{self.local_data_dir}{file_name}' do not exist.",
                file=sys.stderr,
            )
            exit(1)
        process = subprocess.run(
            f"mv --verbose -i {file_name} {self.local_srv_upload_dir}",
            shell=True,
            text=True,
            check=True,
            timeout=10,
        )

    ##################################CLIENT#################################

    ###SENDING
    def send_file(self, name_file):
        """We verify that's the file we want to send and 'local_data_dir' do exists"""
        if not os.path.exists(f"{self.local_data_dir}{name_file}"):
            print(
                f"The local file '{self.local_data_dir}{name_file}' do not exist.",
                file=sys.stderr,
            )
            exit(1)

        try:
            """Connection with sftp server"""
            sftpProcess = pexpect.spawn(
                f"{self.client_ssh_exec} -F {self.client_config_file}  {self.username}@{self.server_ip}"
            )

            """wait for the connexion to be down, and for the SFTP interface to be launch"""
            sftpProcess.expect("sftp>", timeout=15)
            print("Connexion started")

            """Check existance and moove to the directory where we want to send the file"""
            sftpProcess.sendline(f"cd {self.remote_client_upload_dir}")
            index = sftpProcess.expect(
                [
                    f"realpath {self.remote_client_upload_dir}: No such file",
                    "stat remote: No such file or directory",
                    "Permission denied",
                    "sftp>",
                ],
                timeout=15,
            )
            if index == 0 or index == 1:
                print(
                    f"The directory {self.remote_client_upload_dir} does not exist",
                    file=sys.stderr,
                )
                exit(1)
            if index == 2:
                print(
                    f"Permission denied : The directory {self.client_upload_dir} is not accessible.",
                    file=sys.stderr,
                )
                exit(1)

            """upload the file"""
            sftpProcess.sendline(f"lcd {self.local_data_dir}")
            sftpProcess.expect("sftp>")
            sftpProcess.sendline("ls")
            # wait for the list of file
            sftpProcess.expect("sftp>")
            # Recuperation of the list of file and conversion in list
            file_list = (
                sftpProcess.before.decode()
                .translate({ord("\r"): " ", ord("\n"): " "})
                .replace("\n", " ")
                .split()[1::]
            )

            already_upload = False
            if f"{name_file}.tmp" in file_list:
                # if the file we want to send existe in the remote server, it means that we add to finish the download
                print(f"{name_file}.tmp already on the distant server : ")
                sftpProcess.sendline(f"reput {name_file} {name_file}.tmp")
                print(f"reput {name_file} -> {name_file}.tmp")
            elif f"{name_file}" in file_list:
                # It means that we have already upload this file
                print(f"{name_file} was already on the distant server : ")
                already_upload = True
            else:
                # if the file we want to send do not existe in the remote server, we just add it.
                sftpProcess.sendline(f"put {name_file} {name_file}.tmp")
                print(f"{name_file} -> {name_file}.tmp")

            if not already_upload:
                index = sftpProcess.expect(
                    [
                        "Permission denied",
                        "100%",
                        "destination file same size or larger",
                    ],
                    timeout=60,
                )
                if index == 0:
                    print(
                        "Permission denied :\n "
                        + sftpProcess.before.decode("utf-8")
                        + sftpProcess.after.decode("utf-8"),
                        file=sys.stderr,
                    )
                    exit(1)

                if index == 1 or index == 2:
                    print(f"The file {name_file} is uploaded")
                    sftpProcess.sendline(f"rename {name_file}.tmp {name_file}")

            """Kill the connexion with the serveur"""
            sftpProcess.sendline("quit")
            sftpProcess.expect(pexpect.EOF)
            sftpProcess.kill(0)
            print(sftpProcess.before.decode("utf-8"))
            print("File transfer : Success")

        except pexpect.EOF:
            print(
                "SFTP connexion has been interrupted : \n"
                + sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)
        except pexpect.TIMEOUT:
            print(
                "SFTP connexion has expired : \n" + sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)
        except Exception as e:
            print(
                f"An error occure during SFTP connexion :\n {str(e)}\n", file=sys.stderr
            )
            print(
                sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)

    def send_mult_files(self, list_of_files):
        """We verify that's ALL the files do exists"""
        for file in list_of_files:
            if not os.path.exists(f"{self.local_data_dir}{file}"):
                print(
                    f"The local file '{self.local_data_dir}{file}' do not exist.",
                    file=sys.stderr,
                )
                exit(1)

        try:
            """Connection with sftp server"""
            sftpProcess = pexpect.spawn(
                f"{self.client_ssh_exec} -F {self.client_config_file}  {self.username}@{self.server_ip}"
            )

            """wait for the connexion to be down, and for the SFTP interface to be launch"""
            sftpProcess.expect("sftp>", timeout=15)
            print("Connexion started")

            """Existance + moove to the directory where we want to send the files"""
            sftpProcess.sendline(f"cd {self.remote_client_upload_dir}")
            index = sftpProcess.expect(
                [
                    f"realpath {self.remote_client_upload_dir}: No such file",
                    "stat remote: No such file or directory",
                    "Permission denied",
                    "sftp>",
                ],
                timeout=15,
            )
            if index == 0 or index == 1:
                print(
                    f"The directory {self.remote_client_upload_dir} does not exist",
                    file=sys.stderr,
                )
                exit(1)
            if index == 2:
                print(
                    f"Permission denied : The directory {self.remote_client_upload_dir} is not accessible.",
                    file=sys.stderr,
                )
                exit(1)

            sftpProcess.sendline(f"lcd {self.local_data_dir}")
            sftpProcess.expect("sftp>")
            """Create the list of the files already present on the distant server"""
            sftpProcess.sendline("ls")
            # wait for the list of file
            sftpProcess.expect("sftp>")
            # Recuperation of the list of file and conversion in list
            file_list = (
                sftpProcess.before.decode()
                .translate({ord("\r"): " ", ord("\n"): " "})
                .replace("\n", " ")
                .split()[1::]
            )

            """upload files"""
            for file in list_of_files:
                already_upload = False
                if f"{file}.tmp" in file_list:
                    # if the file we want to send existe in the remote server, it means that we add to finish the download
                    print(f"{file}.tmp already on the distant server : ")
                    sftpProcess.sendline(f"reput {file} {file}.tmp")
                    print(f"reput {file} -> {file}.tmp")
                elif f"{file}" in file_list:
                    # It means that we have already upload this file
                    print(f"{file} was already on the distant server : ")
                    already_upload = True
                else:
                    # if the file we want to send do not existe in the remote server, we just add it.
                    sftpProcess.sendline(f"put {file} {file}.tmp")
                    print(f"put{file} -> {file}.tmp")

                if not already_upload:
                    index = sftpProcess.expect(
                        [
                            "Permission denied",
                            "100%",
                            "destination file same size or larger",
                        ],
                        timeout=60,
                    )
                    if index == 0:
                        print(
                            "Permission denied :\n "
                            + sftpProcess.before.decode("utf-8")
                            + sftpProcess.after.decode("utf-8"),
                            file=sys.stderr,
                        )
                        exit(1)
                    
                    if index == 1 or index == 2:
                        print(f"The file {file} is uploaded")
                        sftpProcess.sendline(f"rename {file}.tmp {file}")
                        sftpProcess.expect("sftp>", timeout=15)

            """Kill the connexion with the serveur"""
            sftpProcess.sendline("quit")
            sftpProcess.expect(pexpect.EOF)
            sftpProcess.kill(0)
            print(sftpProcess.before.decode("utf-8"))
            print("Files transfer : Success")

        except pexpect.EOF:
            print(
                "SFTP connexion has been interrupted : \n"
                + sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)
        except pexpect.TIMEOUT:
            print(
                "SFTP connexion has expired : \n" + sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)
        except Exception as e:
            print(
                f"An error occure during SFTP connexion :\n {str(e)}\n", file=sys.stderr
            )
            print(
                sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)

    ###GETTING
    def get_file(self, name_file):
        """We verify that's 'local_data_dir' do exists"""
        if not os.path.exists(f"{self.local_data_dir}"):
            print(
                f"The local directory '{self.local_data_dir}' do not exist.",
                file=sys.stderr,
            )
            exit(1)

        try:
            sftpProcess = pexpect.spawn(
                f"{self.client_ssh_exec} -F {self.client_config_file}  {self.username}@{self.server_ip}"
            )
            sftpProcess.expect("sftp>", timeout=15)
            print("Connexion started")

            """check existences of the directories"""
            sftpProcess.sendline(f"lcd {self.local_data_dir}")
            sftpProcess.sendline(f"cd {self.remote_srv_upload_dir}")
            index = sftpProcess.expect(
                [
                    f"realpath {self.remote_srv_upload_dir}: No such file",
                    "stat remote: No such file or directory",
                    "Permission denied",
                    "sftp>",
                ],
                timeout=15,
            )
            if index == 0 or index == 1:
                print(
                    f"The directory {self.remote_srv_upload_dir} does not exist",
                    file=sys.stderr,
                )
                exit(1)
            if index == 2:
                print(
                    f"Permission denied : The directory {self.remote_client_upload_dir} is not accessible.",
                    file=sys.stderr,
                )
                exit(1)

            """get the file"""
            # With reget, we don't have to seperate the case, it's gonna get the file anyway
            sftpProcess.sendline(f"reget {name_file}")
            index = sftpProcess.expect(
                ["not found", "Permission denied", "100%"], timeout=60
            )
            if index == 0:
                print(
                    f"The file {self.remote_srv_upload_dir}{name_file} not found",
                    file=sys.stderr,
                )
                exit(1)
            if index == 1:
                print(
                    f"Permission denied : can't download the file {self.remote_srv_upload_dir}{name_file}",
                    file=sys.stderr,
                )
                exit(1)

            """stop the connexion"""
            sftpProcess.sendline("exit")
            sftpProcess.expect(pexpect.EOF)
            sftpProcess.kill(0)
            print(sftpProcess.before.decode("utf-8"))
            if os.path.exists(f"{self.local_data_dir}{name_file}"):
                print("File transfer : Success")

        except pexpect.EOF:
            print(
                "SFTP connexion has been interrupted : \n"
                + sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)
        except pexpect.TIMEOUT:
            print(
                "SFTP connexion has expired : \n" + sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)
        except Exception as e:
            print(
                f"An error occure during SFTP connexion : \n{str(e)}\n", file=sys.stderr
            )
            print(
                sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)

    def get_mult_files(self, list_of_files):
        """We verify that's 'local_data_dir' do exists"""
        if not os.path.exists(f"{self.local_data_dir}"):
            print(
                f"The local directory '{self.local_data_dir}' do not exist.",
                file=sys.stderr,
            )
            exit(1)

        try:
            sftpProcess = pexpect.spawn(
                f"{self.client_ssh_exec} -F {self.client_config_file}  {self.username}@{self.server_ip}"
            )
            sftpProcess.expect("sftp>", timeout=15)
            print("Connexion started")

            """get the files"""
            sftpProcess.sendline(f"lcd {self.local_data_dir}")
            sftpProcess.sendline(f"cd {self.remote_srv_upload_dir}")
            index = sftpProcess.expect(
                [
                    f"realpath {self.remote_srv_upload_dir}: No such file",
                    "stat remote: No such file or directory",
                    "Permission denied",
                    "sftp>",
                ],
                timeout=15,
            )
            if index == 0 or index == 1:
                print(
                    f"The directory {self.remote_srv_upload_dir} does not exist",
                    file=sys.stderr,
                )
                exit(1)
            if index == 2:
                print(
                    f"Permission denied : The directory {self.remote_srv_upload_dir} is not accessible.",
                    file=sys.stderr,
                )
                exit(1)

            for file in list_of_files:
                sftpProcess.sendline(f"reget {file}")
                index = sftpProcess.expect(
                    ["not found", "Permission denied", "100%"], timeout=60
                )
                if index == 0:
                    print(
                        f"The file {self.remote_srv_upload_dir}{file} not found",
                        file=sys.stderr,
                    )
                    exit(1)
                if index == 1:
                    print(
                        f"Permission denied : can't download the file {self.remote_srv_upload_dir}{file}",
                        file=sys.stderr,
                    )
                    exit(1)

            """stop the connexion"""
            sftpProcess.sendline("exit")
            sftpProcess.expect(pexpect.EOF)
            sftpProcess.kill(0)
            print(sftpProcess.before.decode("utf-8"))
            for file in list_of_files:
                if not os.path.exists(f"{self.local_data_dir}{file}"):
                    print(
                        f"Error, one of the files wanted was not downloaded : missing {self.local_data_dir}{file}",
                        file=sys.stderr,
                    )
                    exit(1)
            print("Files transfer : Success")

        except pexpect.EOF:
            print(
                "SFTP connexion has been interrupted : \n"
                + sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)
        except pexpect.TIMEOUT:
            print(
                "SFTP connexion has expired : \n" + sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)
        except Exception as e:
            print(
                f"An error occure during SFTP connexion : \n{str(e)}\n", file=sys.stderr
            )
            print(
                sftpProcess.before.decode("utf-8"),
                file=sys.stderr,
            )
            exit(1)


######################OTHER FUNCTIONS and CLASSES#########################


class MyEventHandler(FileSystemEventHandler):
    """
    TODO : IMPROVE IT ACCORDING TO THE PROTOCOL TO USE !!
    add a signal script that send an information to
    the main thread when a file or a dir appear.

    C.F the source code of FileSystemEventHandler and overwrite
    events and adapte them to our class.
    """

    def __init__(self, communication_module_server):
        super().__init__()
        self.communication_module_server = communication_module_server

    def on_created(self, event):
        if event.is_directory:
            print(f"Directory created : {event.src_path}")
        else:
            print(f"File created : {event.src_path}")

    def on_deleted(self, event):
        """
        TODO : add a security here, in case we want to delete a file or a dir
        which is not in dirs_from_client or files_from_client
        Or just use discard that works like remove but without raising an error in
        case the element does not exist in the list.
        """
        if event.is_directory:
            print(f"Directory deleted : {event.src_path}")
        else:
            print(f"File deleted : {event.src_path}")

    def on_modified(self, event):
        "TODO : add some security controle here"

    def on_moved(self, event):
        if event.is_directory:
            print(f"directory move from {event.src_path} to {event.dest_path}")
        else:
            print(f"file move from {event.src_path} to {event.dest_path}")


def get_IP():
    """
    return the IP adresse of the current machin (in string format)pass
    """
    p1 = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE)
    result = subprocess.run(
        ["awk", "{print $2}"], stdin=p1.stdout, capture_output=True, check=True
    )
    return result.stdout[0:-1].decode()
