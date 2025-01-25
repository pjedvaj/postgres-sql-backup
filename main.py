#!/usr/bin/env python3

import os
import platform
import smtplib
import glob
import re
import yaml
import time
import paramiko
from datetime import datetime
from subprocess import PIPE,Popen

# Settings
config = yaml.safe_load(open('./config.yml'))

# Date and time for backup filename
timestamp = datetime.now().strftime(config['date_format'])

# Local backup of database
def backup():
    command = config['command'] + config['folder_path'] + config['backup_name'] + timestamp + config['extension']\
    
    p = Popen(command, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    return p.communicate()

backup()

# Waiting for local backup to finish
while os.path.isfile(config['folder_path'] + config['backup_name'] + timestamp + config['extension']) != True:
    print('Waiting for local backup to finish.')
    time.sleep(1)
else:
	print('Local backup is finished.')

# Get the size of last local backup file
folder_path = config['folder_path']
file_type = r'/*' + config['extension']
files = glob.glob(folder_path + file_type)
backup_file = max(files, key=os.path.getctime)
filename = re.sub(folder_path, '', backup_file)
file_size = str(os.path.getsize(backup_file))
print(backup_file + ' : ' + file_size)

# Send mail in case of problems with backup
def mail():
    location = platform.node()
    sender_add=config['sender_add']
    receiver_add=config['receiver_add']
    password=config['mail_password']
    smtp_server=smtplib.SMTP(config['smtp_server'], config['smtp_port'])
    smtp_server.ehlo()
    smtp_server.starttls()
    smtp_server.ehlo()
    smtp_server.login(sender_add, password)
    msg_to_be_sent ='Backup script on server ' + location + ' failed to execute backup.'
    smtp_server.sendmail(sender_add, receiver_add,msg_to_be_sent)
    smtp_server.quit()

if (file_size == '0'):
    mail()

# Copying of backup to remote computer
else:
    host = config['sftp_host']
    username = config['sftp_username']
    password = config['sftp_password']
    try:
        t = paramiko.Transport((host, 22))
        t.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(t)
        sftp.put(backup_file, config['sftp_path'] + filename)
        print('Backup was successfully copied to remote computer.')
    except:
        print('Remote computer for backup is not accessible, mail with error was sent.')
        mail()