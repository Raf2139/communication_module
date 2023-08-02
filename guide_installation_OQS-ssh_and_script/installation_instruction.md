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

3.Update the path to access OQS-OpenSSH instead of the classic OpenSSH. Add the following line to ~/.bashrc:

```bash
PATH=/usr/local/openssh/bin:$PATH
```

# User and File Directory Partitioning for SFTP:

Next, you can create a directory for the SFTP client following the instructions provided in this link:
https://www.digitalocean.com/community/tutorials/how-to-enable-sftp-without-shell-access-on-ubuntu-20-04

# Python Module Installation:

When installing a Python module (e.g., watchdog), make sure to use "sudo" to ensure proper accessibility when executing scripts with sudo privileges. Superusers have different environments than regular users.

Remember to execute your scripts with "sudo" privilege to access all required modules properly.

Following these steps will help you install and configure OQS-OpenSSH on your Ubuntu 20 system.

