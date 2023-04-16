from flask import Flask, abort, make_response, jsonify
import utils as utils

app = Flask(__name__)
utils.startLookup()

@app.route("/")
def getDeviceList():
  utils.secretGuard()
  return utils.getDeviceList(True)

@app.route("/<deviceId>")
def getDeviceInfo(deviceId):
  utils.secretGuard()
  deviceInfo = utils.getDeviceInfo(deviceId)
  if not deviceInfo:
    abort(make_response(jsonify(message="Device not found."), 404))
  return deviceInfo

@app.route("/<deviceId>/on")
def turnOn(deviceId):
  utils.secretGuard()
  device = utils.getDevice(deviceId)
  if not device:
    abort(make_response(jsonify(message="Device not found."), 404))
  device.handshake()
  device.login()
  device.turnOn()
  return { "status": "ok" }

@app.route("/<deviceId>/off")
def turnOff(deviceId):
  utils.secretGuard()
  device = utils.getDevice(deviceId)
  if not device:
    abort(make_response(jsonify(message="Device not found."), 404))
  device.handshake()
  device.login()
  device.turnOff()
  return { "status": "ok" }
