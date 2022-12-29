import subprocess
import requests
import os
import uuid
import threading
import time
from PyP100 import PyP100
from dotenv import load_dotenv
load_dotenv()

tapoEmail = os.getenv('TAPO_EMAIL')
tapoPassword = os.getenv('TAPO_PASSWORD')
deviceList = []
deviceDict = {}

def ping(ip):
    result = subprocess.run(['ping', '-c', '1', ip], stdout=subprocess.PIPE)
    return result.returncode == 0

def startLookup():
    threading.Thread(target=lookupPass).start()

def lookupPass():
    ip = subprocess.run(['ipconfig', 'getifaddr', 'en0'], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    mask = ip[:ip.rfind('.') + 1]
    for i in range(1, 255):
        deviceIp = mask + str(i)
        threading.Thread(target=ping, args=(deviceIp,)).start()
    time.sleep(100)
    startLookup()

def getNetworkDevicesMacMap():
    arpResult = subprocess.run(['arp', '-a', '-i', 'en0'], stdout=subprocess.PIPE)
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
        device['deviceIp'] = macMap[deviceMac] if deviceMac in macMap else None
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
