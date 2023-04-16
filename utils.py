import subprocess
import requests
import os
import uuid
import threading
import time
import base64
import csv
import socket
from flask import request, abort, make_response, jsonify
from PyP100 import PyP100
from dotenv import load_dotenv
load_dotenv()

tapoEmail = os.getenv('TAPO_EMAIL')
tapoPassword = os.getenv('TAPO_PASSWORD')
secret = os.getenv('SECRET')
autoDiscover = os.getenv('AUTO_DISCOVER') == 'true'
deviceList = []
deviceDict = {}
deviceStaticIps = {}

if os.path.exists("static_ips.csv"):
    with open("static_ips.csv", "r") as infile:
        reader = csv.reader(infile)
        next(reader, None)  # skip the headers
        for row in reader:
            deviceStaticIps[row[0].lower()] = row[1]
    print("Static IPs loaded: " + str(deviceStaticIps))

def ping(ip):
    result = subprocess.run(['ping', '-c', '1', ip], stdout=subprocess.PIPE)
    return result.returncode == 0

def startLookup():
    if autoDiscover:
        threading.Thread(target=lookupPass).start()

def lookupPass():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    mask = ip[:ip.rfind('.') + 1]
    for i in range(1, 255):
        deviceIp = mask + str(i)
        threading.Thread(target=ping, args=(deviceIp,)).start()
    time.sleep(100)
    startLookup()

def getNetworkDevicesMacMap():
    arpResult = subprocess.run(['arp', '-a'], stdout=subprocess.PIPE)
    arpList = arpResult.stdout.decode('utf-8').split('\n')
    result = {}
    for arp in arpList:
        if arp:
            arp = arp.split(' ')
            atIdx = arp.index('at')
            mac = ''.join(['0' + i if len(i) == 1 else i for i in arp[atIdx + 1].split(':')]).lower()
            ip = arp[atIdx - 1][1:-1]
            result[mac] = ip
    return result


def getToken():
	url = "https://eu-wap.tplinkcloud.com"
	payload = {
		"method": "login",
		"params": {
			"appType": "Tapo_Ios",
			"cloudUserName": tapoEmail,
			"cloudPassword": tapoPassword,
			"terminalUUID": str(uuid.uuid4())
		}
	}

	return requests.post(url, json=payload).json()['result']['token']

def getDeviceList(refresh = False):
    global deviceList, deviceDict
    if not refresh and len(deviceList):
        return deviceList

    URL = "https://eu-wap.tplinkcloud.com?token=" + getToken()
    Payload = {
	    "method": "getDeviceList",
    }
    httpResult = requests.post(URL, json=Payload).json()['result']['deviceList']
    result = []
    macMap = getNetworkDevicesMacMap()
    for device in httpResult:
        deviceMac = device['deviceMac'].lower()
        device['deviceIp'] = deviceStaticIps[deviceMac] if deviceMac in deviceStaticIps else macMap[deviceMac] if deviceMac in macMap else None
        try: 
            device['alias'] = (base64.b64decode(device['alias'])).decode('utf-8')
        except:
            pass
        result.append(device)
    
    deviceList = result
    deviceDict = { deviceList[i]['deviceId'] : deviceList[i] for i in range(0, len(deviceList) )}
    return result

def getDeviceInfo(deviceId):
    if deviceId in deviceDict:
        return deviceDict[deviceId]
    else:
        getDeviceList(True)
        return deviceDict[deviceId] if deviceId in deviceDict else None

def getDevice(deviceId):
    deviceInfo = getDeviceInfo(deviceId)
    if deviceInfo:
        return PyP100.P100(deviceInfo['deviceIp'], tapoEmail, tapoPassword)
    else:
        return None

def secretGuard():
    if secret and request.headers.get('Authorization') != 'Bearer ' + secret:
        abort(make_response(jsonify(message="Unauthorized."), 401))