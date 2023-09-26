import requests
import sys
import logging
import json
from time import sleep

class SmartHomeController:
  ipAddress = None
  shutterDevices = []
  appId = None
  pollingId = None
  
  def fetchOpenWindows(self):
    self.openWindows = []
    url = "https://" + self.ipAddress + ":8444/smarthome/doors-windows/openwindows"

    payload = {}
    headers = {
      'Content-Type': 'application/json',
      'api-version': '3.2'
    }

    response = requests.request("GET", 
      url, headers=headers, data=payload, verify=False,
      cert=(".ssl/client-cert.pem", ".ssl/client-key.pem") 
    )
    if "openWindows" in response.json():
      self.openWindows = response.json()["openWindows"]

    return True

  def anyWindowsOpen(self):
    return self.openWindows.count() > 0

  def initLongPolling(self):
    url = "https://" + self.ipAddress + ":8444/remote/json-rpc"

    payload = json.dumps([
      {
        "jsonrpc": "2.0",
        "method": "RE/subscribe",
        "params": [
          "com/bosch/sh/remote/*",
          None
        ]
      }
    ])
    headers = {
      'Content-Type': 'application/json',
      'api-version': '3.2'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False,
      cert=(".ssl/client-cert.pem", ".ssl/client-key.pem"))
    self.pollingId = response.json()[0]["result"]

  def poll(self):
    url = "https://" + self.ipAddress + ":8444/remote/json-rpc"

    payload = json.dumps([
      {
        "jsonrpc": "2.0",
        "method": "RE/longPoll",
        "params": [
          self.pollingId,
          10
        ]
      }
    ])
    headers = {
      'Content-Type': 'application/json',
      'api-version': '3.2'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False,
      cert=(".ssl/client-cert.pem", ".ssl/client-key.pem"))
    if len( response.json()[0]["result"]) != 0:
      self.fetchOpenWindows()
    return True

  def __init__(self, ipAddress):
    self.ipAddress = ipAddress


class OpenWeatherMap:
  lat = 0
  lon = 0
  apiKey = None

  def getCurrentWeather(self):
    url = "https://api.openweathermap.org/data/2.5/weather?lat=" + self.lat + "&lon=" + self.lat + "&appid=" + self.apiKey

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()["weather"][0]["main"]

  def __init__(self, lat, lon, apiKey):
    self.lat = lat
    self.lon = lon


def main() -> int:
  logging.basicConfig(level=logging.INFO)
  owm = OpenWeatherMap(52.208397, 7.316489, "05740d25baa66c3df0824fc3391f57f5")
  shc = SmartHomeController("192.168.22.136")
  shc.fetchOpenWindows()
  shc.initLongPolling()
  while shc.poll():
    if shc.anyWindowsOpen:
      logging.info("Windows are open.")
      logging.info("Open windows:")
      for window in shc.openWindows:
        logging.info("- " + window["name"])
      # check weather
      logging.info("Current weather condition: " + shc.getCurrentWeather())
      # in case of rain or snow
      # send message to recipients
    else:
      logging.info("No windows open.")

if __name__ == '__main__':
  sys.exit(main())  