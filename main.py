from utils import getNetworkDevicesMacMap, getDevice, getDeviceInfo, startLookup
startLookup()

info = getDeviceInfo("8022116E8E7698E841D4FF58F1620CD21FD1B26C")
print(info)
p100 = getDevice("8022116E8E7698E841D4FF58F1620CD21FD1B26C")

p100.handshake() #Creates the cookies required for further methods
p100.login() #Sends credentials to the plug and creates AES Key and IV for further methods

p100.turnOn()
