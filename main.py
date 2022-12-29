from flask import Flask
import utils as utils

app = Flask(__name__)
utils.startLookup()

@app.route("/")
def getDeviceList():
  return utils.getDeviceList(True)

@app.route("/<deviceId>")
def getDeviceInfo(deviceId):
  return utils.getDeviceInfo(deviceId)

@app.route("/<deviceId>/on")
def turnOn(deviceId):
  device = utils.getDevice(deviceId)
  device.handshake()
  device.login()
  device.turnOn()
  return { "status": "ok" }

@app.route("/<deviceId>/off")
def turnOff(deviceId):
  device = utils.getDevice(deviceId)
  device.handshake()
  device.login()
  device.turnOff()
  return { "status": "ok" }
