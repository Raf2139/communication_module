#! /usr/bin/python3

"""
This file gonna define the class "CommunicationModule" and 2
subClass (server, client) that gonna be use for alice en bob 
communication.
Alice will be rpz by an instance of "CommunicationModuleClient"
and Bob by an instance of "CommunicationModuleServer"
"""


import pexpect  # To lanch a process and deal with it (better than "subprocess" for SFTP comand line interaction)
import yaml  # To importe and deal with the .yaml that we will use as config file
from abc import ABC  # Allow us to create an abstract class (C.F CommunicationModule)
import subprocess
import glob  # For searching if a file exit using regexp
import threading  # For multithreading and deamons
import time  # For make the deamons sleep
import sys

# Import 'watchdog'. For the server monitoring
# of the files uploading by the client
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class CommunicationModule(ABC):
    def __init__(
        self,
        server_ip,
        ssh_exec,
        config_file,
        client_upload_dir,
        srv_upload_dir,
        local_data_dir,
    ):
        self.ssh_exec = ssh_exec  # path to the ssh client or server
        self.server_ip = server_ip
        self.client_upload_dir = client_upload_dir
        self.srv_upload_dir = srv_upload_dir
        self.config_file = config_file
        self.local_data_dir = local_data_dir

    def __str__(self):
        """
        We defined the __str__ methods because we gonna
        use it for debugging.
        """
        string_to_return = (
            f"ssh_exec : {self.ssh_exec}\n"
            f"server_ip : {self.server_ip}\n"
            f"client_upload_dir : {self.client_upload_dir}\n"
            f"srv_upload_dir : {self.srv_upload_dir}\n"
            f"config_file : {self.config_file}\n"
            f"local_data_dir : {self.local_data_dir}"
        )
        return string_to_return

    def send_file(self, file_name):
        pass

    def read_file(self, file_name):
        pass

    def send_mult_files(self, list_of_files):
        """
        TODO : change all the names according to this one
        """
        pass

    def read_files(self, list_of_files):
        pass


#################################SERVER#################################


class CommunicationModuleServer(CommunicationModule):
    def __init__(self, config_file="./config_server.yaml"):
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        super().__init__(
            config["server_ip"],
            config["ssh_exec"],
            config["config_file"],
            config["client_upload_dir"],
            config["srv_upload_dir"],
            config["local_data_dir"],
        )
        self.time_to_live = config["time_to_live"]
        self.server_on = False
        self.dirs_from_client = set()
        self.files_from_client = set()

    def __str__(self):
        return (
            super().__str__()
            + f"\ntime_to_live : {self.time_to_live}"
            + f"\nserver_on : {self.server_on}"
            + f"\ndirs_from_client : {self.dirs_from_client}"
            + f"\nfiles_from_client : {self.files_from_client}"
        )

    def client_upload_monitoring_deamon(self):
        """
        TODO : finish to right properly this part and add it to the methodes
        start_server
        """
        my_event_handler = MyEventHandler(self)
        my_observer = Observer()
        my_observer.schedule(
            event_handler=my_event_handler, path=self.client_upload_dir, recursive=True
        )
        my_observer.start()
        living_time = 0
        while living_time < self.time_to_live:
            time.sleep(1)
            living_time += 1
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
            subprocess.run(["kill", f"{ssh_pid}"], check=True)
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
                f"{self.ssh_exec}",
                "-f",
                f"{self.config_file}",
                option,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

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

        # start the watchdog on the directory of upload of the client
        self.client_upload_monitoring_deamon()
        # stop the server once the ttl is reach.
        self.stop_server()

    def send_file(self, file_name):
        if not glob.glob(f"{self.local_data_dir}{file_name}"):
            print(
                f"The local file '{self.local_data_dir}{file_name}' do not exist.",
                file=sys.stderr,
            )
            exit(1)
        process = subprocess.run(
            f"mv --verbose -i {file_name} {self.srv_upload_dir}",
            shell=True,
            text=True,
            check=True,
            timeout=10,
        )

    def read_file(self, file_name):
        """
        TODO : decide what we should do once the file is found or once the time_to_wait is reach
        """

##################################CLIENT#################################


class CommunicationModuleClient(CommunicationModule):
    def __init__(self, config_file="config_client.yaml"):
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        super().__init__(
            config["server_ip"],
            config["ssh_exec"],
            config["config_file"],
            config["client_upload_dir"],
            config["srv_upload_dir"],
            config["local_data_dir"],
        )
        self.username = config["username"]

    def __str__(self):
        return super().__str__() + f"\nusername : {self.username}"

    def send_file(self, name_file):
        """We verify that's the file we want to send and 'local_data_dir' do exists"""
        if not glob.glob(f"{self.local_data_dir}{name_file}"):
            print(
                f"The local file '{self.local_data_dir}{name_file}' do not exist.",
                file=sys.stderr,
            )
            exit(1)

        try:
            """Connection with sftp server"""
            sftpProcess = pexpect.spawn(
                f"{self.ssh_exec} -F {self.config_file}  {self.username}@{self.server_ip}"
            )

            """wait for the connexion to be down, and for the SFTP interface to be launch"""
            sftpProcess.expect("sftp>", timeout=10)
            print("Connexion started")

            """Check existance and moove to the directory where we want to send the file"""
            sftpProcess.sendline(f"cd {self.client_upload_dir}")
            index = sftpProcess.expect(
                [
                    f"realpath {self.client_upload_dir}: No such file",
                    "stat remote: No such file or directory",
                    "Permission denied",
                    "sftp>",
                ],
                timeout=10,
            )
            if index == 0 or index == 1:
                print(
                    f"The directory {self.client_upload_dir} does not exist",
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
            sftpProcess.sendline(f"ls {name_file}")
            index = sftpProcess.expect([f"{name_file}", "not found"], timeout=10)

            if index == 0:
                # if the file we want to send existe in the remote server, it means that we add to finish the download
                print(f"{name_file} already on the distant server : ")
                sftpProcess.sendline(f"reput {name_file}")
                print(f"reput {name_file}")
            else:
                # if the file we want to send do not existe in the remote server, we just add it.
                sftpProcess.sendline(f"put {name_file}")
                print(f"put {name_file}")

            index = sftpProcess.expect(
                [
                    "Permission denied",
                    "100%",
                    "destination file same size or larger",
                ],
                timeout=10,
            )
            if index == 0:
                print(
                    "Permission denied :\n "
                    + sftpProcess.before.decode("utf-8")
                    + sftpProcess.after.decode("utf-8"),
                    file=sys.stderr,
                )
                exit(1)

            if index == 2:
                print(f"The file {name_file} was already uploaded")

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

    def read_file(self, name_file):
        """We verify that's 'local_data_dir' do exists"""
        if not glob.glob(f"{self.local_data_dir}"):
            print(
                f"The local directory '{self.local_data_dir}' do not exist.",
                file=sys.stderr,
            )
            exit(1)

        try:
            sftpProcess = pexpect.spawn(
                f"{self.ssh_exec} -F {self.config_file}  {self.username}@{self.server_ip}"
            )
            sftpProcess.expect("sftp>", timeout=10)
            print("Connexion started")

            """check existences of the directories"""
            sftpProcess.sendline(f"lcd {self.local_data_dir}")
            sftpProcess.sendline(f"cd {self.srv_upload_dir}")
            index = sftpProcess.expect(
                [
                    f"realpath {self.client_upload_dir}: No such file",
                    "stat remote: No such file or directory",
                    "Permission denied",
                    "sftp>",
                ]
            )
            if index == 0 or index == 1:
                print(
                    f"The directory {self.client_upload_dir} does not exist",
                    file=sys.stderr,
                )
                exit(1)
            if index == 2:
                print(
                    f"Permission denied : The directory {self.client_upload_dir} is not accessible.",
                    file=sys.stderr,
                )
                exit(1)

            """get the file"""
            # With reget, we don't have to seperate the case, it's gonna get the file anyway
            sftpProcess.sendline(f"reget {name_file}")
            index = sftpProcess.expect(
                ["not found", "Permission denied", "100%"], timeout=10
            )
            if index == 0:
                print(
                    f"The file {self.srv_upload_dir}{name_file} not found",
                    file=sys.stderr,
                )
                exit(1)
            if index == 1:
                print(
                    f"Permission denied : can't download the file {self.srv_upload_dir}{name_file}",
                    file=sys.stderr,
                )
                exit(1)

            """stop the connexion"""
            sftpProcess.sendline("exit")
            sftpProcess.expect(pexpect.EOF)
            sftpProcess.kill(0)
            print(sftpProcess.before.decode("utf-8"))
            if glob.glob(f"{self.local_data_dir}{name_file}"):
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

    def send_files(self, list_of_files):
        """We verify that's ALL the files do exists"""
        for file in list_of_files:
            if not glob.glob(f"{self.local_data_dir}{file}"):
                print(
                    f"The local file '{self.local_data_dir}{file}' do not exist.",
                    file=sys.stderr,
                )
                exit(1)

        try:
            """Connection with sftp server"""
            sftpProcess = pexpect.spawn(
                f"{self.ssh_exec} -F {self.config_file}  {self.username}@{self.server_ip}"
            )

            """wait for the connexion to be down, and for the SFTP interface to be launch"""
            sftpProcess.expect("sftp>", timeout=10)
            print("Connexion started")

            """Existance + moove to the directory where we want to send the files"""
            sftpProcess.sendline(f"cd {self.client_upload_dir}")
            index = sftpProcess.expect(
                [
                    f"realpath {self.client_upload_dir}: No such file",
                    "stat remote: No such file or directory",
                    "Permission denied",
                    "sftp>",
                ]
            )
            if index == 0 or index == 1:
                print(
                    f"The directory {self.client_upload_dir} does not exist",
                    file=sys.stderr,
                )
                exit(1)
            if index == 2:
                print(
                    f"Permission denied : The directory {self.client_upload_dir} is not accessible.",
                    file=sys.stderr,
                )
                exit(1)

            """upload files"""
            sftpProcess.sendline(f"lcd {self.local_data_dir}")
            for file in list_of_files:
                sftpProcess.sendline(f"ls {file}")
                index = sftpProcess.expect([f"{file}", "not found"], timeout=10)

                if index == 0:
                    # if the file we want to send existe in the remote server, it means that we add to finish the download
                    print(f"{file} already on the distant server : ")
                    sftpProcess.sendline(f"reput {file}")
                    print(f"reput {file}")
                else:
                    # if the file we want to send do not existe in the remote server, we just add it.
                    sftpProcess.sendline(f"put {file}")
                    print(f"put {file}")

                index = sftpProcess.expect(
                    [
                        "Permission denied",
                        "100%",
                        "destination file same size or larger",
                    ],
                    timeout=10,
                )
                if index == 0:
                    print(
                        "Permission denied :\n "
                        + sftpProcess.before.decode("utf-8")
                        + sftpProcess.after.decode("utf-8"),
                        file=sys.stderr,
                    )
                    exit(1)

                if index == 2:
                    print(f"The file {file} was already uploaded")

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

    def read_files(self, list_of_files):
        """We verify that's 'local_data_dir' do exists"""
        if not glob.glob(f"{self.local_data_dir}"):
            print(
                f"The local directory '{self.local_data_dir}' do not exist.",
                file=sys.stderr,
            )
            exit(1)

        try:
            sftpProcess = pexpect.spawn(
                f"{self.ssh_exec} -F {self.config_file}  {self.username}@{self.server_ip}"
            )
            sftpProcess.expect("sftp>", timeout=10)
            print("Connexion started")

            """get the files"""
            sftpProcess.sendline(f"lcd {self.local_data_dir}")
            sftpProcess.sendline(f"cd {self.srv_upload_dir}")
            index = sftpProcess.expect(
                [
                    f"realpath {self.client_upload_dir}: No such file",
                    "stat remote: No such file or directory",
                    "Permission denied",
                    "sftp>",
                ]
            )
            if index == 0 or index == 1:
                print(
                    f"The directory {self.client_upload_dir} does not exist",
                    file=sys.stderr,
                )
                exit(1)
            if index == 2:
                print(
                    f"Permission denied : The directory {self.client_upload_dir} is not accessible.",
                    file=sys.stderr,
                )
                exit(1)

            for file in list_of_files:
                sftpProcess.sendline(f"reget {file}")
                index = sftpProcess.expect(
                    ["not found", "Permission denied", "100%"], timeout=10
                )
                if index == 0:
                    print(
                        f"The file {self.srv_upload_dir}{file} not found",
                        file=sys.stderr,
                    )
                    exit(1)
                if index == 1:
                    print(
                        f"Permission denied : can't download the file {self.srv_upload_dir}{file}",
                        file=sys.stderr,
                    )
                    exit(1)

            """stop the connexion"""
            sftpProcess.sendline("exit")
            sftpProcess.expect(pexpect.EOF)
            sftpProcess.kill(0)
            print(sftpProcess.before.decode("utf-8"))
            for file in list_of_files:
                if not glob.glob(f"{self.local_data_dir}{file}"):
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
    TODO : add a signal script that send an information to
    the main thread when a file or a dir appear.

    C.F the source code of FileSystemEventHandler and overwrite
    events and adapte them to our class.
    """

    def __init__(self, communication_module_server):
        super().__init__()
        self.communication_module_server = communication_module_server

    def on_created(self, event):
        if event.is_directory:
            self.communication_module_server.dirs_from_client.add(event.src_path)
        else:
            self.communication_module_server.files_from_client.add(event.src_path)

    def on_deleted(self, event):
        """
        TODO : add a security here, in case we want to delete a file or a dir
        which is not in dirs_from_client or files_from_client
        Or just use discard that works like remove but without raising an error in
        case the element does not exist in the list.
        """
        if event.is_directory:
            self.communication_module_server.dirs_from_client.remove(event.src_path)
        else:
            self.communication_module_server.files_from_client.remove(event.src_path)

    def on_modified(self, event):
        "TODO : add some security controle here"

    def on_moved(self, event):
        if event.is_directory:
            self.communication_module_server.dirs_from_client.remove(event.src_path)
            self.communication_module_server.dirs_from_client.add(event.dest_path)
        else:
            self.communication_module_server.files_from_client.remove(event.src_path)
            self.communication_module_server.files_from_client.add(event.dest_path)


def get_IP():
    """
    return the IP adresse of the current machin (in string format)pass
    """
    p1 = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE)
    result = subprocess.run(
        ["awk", "{print $2}"], stdin=p1.stdout, capture_output=True, check=True
    )
    return result.stdout[0:-1].decode()
