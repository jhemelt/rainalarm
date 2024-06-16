import requests
import logging
import json
import os
import ssl
import smtplib
from email.message import EmailMessage
from time import sleep
import telegram
import asyncio

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
    return len(self.openWindows) > 0

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
    url = "https://api.openweathermap.org/data/2.5/weather?lat=" + str(self.lat) + "&lon=" + str(self.lon) + "&appid=" + self.apiKey

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()["weather"][0]["main"]

  def __init__(self, lat, lon, apiKey):
    self.lat = lat
    self.lon = lon
    self.apiKey = apiKey

class Messenger:
  subject = ""
  message = ""
  recipients = []
  smtpPassword = ""

  def send(self, subject, message):
    port = 465  # For SSL
    smtp_server = "smtp.strato.de"
    sender_email = "fritzbox@hemelt.info"  # Enter your address
    receiver_email = "juergen@hemelt.info"  # Enter receiver address
    msg = EmailMessage()
    msg["subject"] = subject
    msg["from"] = sender_email
    msg["to"] = receiver_email
    msg.set_content( message )
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, self.smtpPassword)
        server.send_message(msg)

  def __init__(self, smtpPassword):
    self.smtpPassword = smtpPassword

class TelegramMessenger:
  def __init__(self, token, chatId ):
    self.token = token
    self.chatId = chatId
    self.bot = telegram.Bot(token)
  
  async def send(self, message):
    async with self.bot:
        chat = self.bot.get_chat(self.chatId)
        chat.message_auto_delete_time = 300
        await self.bot.send_message(text=message, chat_id=self.chatId )
    


async def main() -> int:
  apiKey = os.environ["API_KEY"]
  smtpPassword = os.environ["SMTP_PASSWORD"]
  token = os.environ["TOKEN"]
  chatId = os.environ["CHATID"]

  logging.basicConfig(level=logging.INFO)
  #messenger = Messenger(smtpPassword)
  messenger = TelegramMessenger(token, chatId)
  owm = OpenWeatherMap(52.208397, 7.316489, apiKey)
  shc = SmartHomeController("192.168.22.136")
  shc.fetchOpenWindows()
  shc.initLongPolling()
  while shc.poll():
    if shc.anyWindowsOpen():
      subject = "Offene Fenster bei Regen"
      message = "Es regnet und es gibt offene Fenster. Folgende Fenster sind offen:\n"
      logging.info("Windows are open.")
      logging.info("Open windows:")
      for window in shc.openWindows:
        logging.info("- " + window["name"] + " in " + window["roomName"])
        message += "- " + window["name"] + " in " + window["roomName"] + "\n"        
      # check weather
      #currentWeather = owm.getCurrentWeather()
      currentWeather = "Rain"
      logging.info("Current weather condition: " + currentWeather)
      # in case of rain or snow
      if currentWeather in ["Rain", "Snow"]:
        # send message to recipients
        # messenger.send( subject, message )
        await messenger.send(message)
        logging.info("Message sent. Sleeping 30 minutes ...")
        sleep(1800)
    else:
      logging.info("No windows open.")


if __name__ == '__main__':
  asyncio.run(main())  