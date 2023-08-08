## Installation Guide for OQS-OpenSSH on Ubuntu 20

This guide will walk you through the installation process for OQS-OpenSSH on Ubuntu 20. Before proceeding, ensure that you have the necessary prerequisites and follow each step carefully.

For more information you can take a look at these following websites: 

For installation instructions of open-quantume-safe library (liboqs) and openssh fork : https://github.com/open-quantum-safe/libssh#build-instructions-for-oqs-openssh 
        
For testing the installations once finish : https://github.com/open-quantum-safe/openssh
        
for setting up a secure folder for the client on a Linux system : https://www.digitalocean.com/community/tutorials/how-to-enable-sftp-without-shell-access-on-ubuntu-20-04 
        

# Prerequisites:

1.Update and upgrade your system:

```bash
sudo apt update -y && sudo apt upgrade -y
```

2.Install Git 

```bash
sudo apt install git
```

3.Install OpenSSL for symmetric encryption algorithm

```bash
sudo apt install openssl
```

4.Install the "classic" version of OpenSSH (server and client) for key exchanges:

```bash
sudo apt install openssh-server
```

(For more information, visit: https://www.cyberciti.biz/faq/ubuntu-linux-install-openssh-server/)

# Install liboqs library:

1.Navigate to the source directory (/usr/local/src) and clone the liboqs repository:

```bash
cd /usr/local/src

git clone --branch main --single-branch --depth 1 https://github.com/open-quantum-safe/liboqs.git
```

2.Install the required packages for liboqs compilation:

```bash
sudo apt install astyle make cmake gcc ninja-build libssl-dev python3-pytest python3-pytest-xdist unzip xsltproc doxygen graphviz python3-yaml valgrind g++ autoconf automake libtool zlib1g-dev
```    

3.Configure and install liboqs library:

```bash
cd /usr/local/src/liboqs/

sudo mkdir build && cd build

sudo cmake -GNinja -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_INSTALL_PREFIX=/usr/local/oqs-lib ..

sudo ninja

sudo ninja install
```

# Install OQS-OpenSSH:

1.Clone the OQS-OpenSSH repository:

```bash
cd /usr/local/src

sudo git clone --branch OQS-v8 --single-branch --depth 1 https://github.com/open-quantum-safe/openssh.git
```

2.Configure and install OQS-OpenSSH:

```bash
cd /usr/local/src/openssh

sudo autoreconf

sudo ./configure --with-libs=-lm --prefix=/usr/local/openssh --sysconfdir=/usr/local/openssh --with-liboqs-dir=/usr/local/oqs-lib

sudo make -j

sudo make install
```

3.[OPTIONAL] Update the path to access OQS-OpenSSH instead of the classic OpenSSH. Add the following line to ~/.bashrc:

```bash
PATH=/usr/local/openssh/bin:$PATH
```


# User and File Directory Partitioning for SFTP:

Next, you can create a directory for the SFTP client. The instructions were found in the following website:
https://www.digitalocean.com/community/tutorials/how-to-enable-sftp-without-shell-access-on-ubuntu-20-04

1.creat a new user, this user gonna be the account of the other participant of the protocol when he gonna want to connect on our server 
This user is going to be named according to you choice (we gonna refer to his name as <remote_qs_sftp_user>)

```bash
sudo adduser <remote_qs_sftp_user>
```

2.Create a folder for this user where his gonna be restricted to:

```bash
sudo mkdir -p /var/sftp/<remote_qs_sftp_user>_folder/uploads
```

3.Give the proper right and acces to this folder (a remote 
account will be able to read and upload file in /var/sftp/<remote_qs_sftp_user>_folder/uploads but he can only read files in the directory /var/sftp/<remote_qs_sftp_user>_folder/. The second directory will be use by the server itself for uploading file for the client)

```bash
sudo chown root:root /var/sftp/<remote_qs_sftp_user>_folder 

sudo chmod 755 /var/sftp/<remote_qs_sftp_user>_folder 

sudo chown <remote_qs_sftp_user>:<remote_qs_sftp_user> /var/sftp/<remote_qs_sftp_user>_folder/uploads 
```

4.Modified the file /usr/local/openssh/sshd_config accoring to the choice made, i.e at the end of the file rewrite as follow the last line : 

```bash
Match User <<remote_qs_sftp_user>
	PubkeyAuthentication yes
	ForceCommand internal-sftp
	PasswordAuthentication no
	ChrootDirectory /var/sftp/<remote_qs_sftp_user>_folder/
	PermitTunnel no
	AllowAgentForwarding yes
	AllowTcpForwarding no
	X11Forwarding no
```


# Python Module Installation:

When installing a Python module (e.g., watchdog), make sure to use "sudo" to ensure proper accessibility when executing scripts with sudo privileges. Superusers have different environments than regular users.

Remember to execute your scripts with "sudo" privilege to access all required modules properly.

Following these steps will help you install and configure OQS-OpenSSH on your Ubuntu 20 system.


# Create a public key ecdsa dilithium :

```bash
 ssh-keygen -t ssh-ecdsa-nistp384-dilithium3
```

# Using a classic ssh connexion to copy the clef on the other on 

```bash
ssh-copy-id -i ~/.ssh/id_ecdsa_nistp384_dilithium3  bob_remote@192.168.202.110 
```

# Replace ssh_config and sshd_config de /usr/local/openssh par ceux du module de communication


# Prendre la nouvelle clef du serveur

./ssh-keygen -R 192.168.202.110
