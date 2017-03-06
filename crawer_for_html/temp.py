import speech
import time

response = speech.input("say something, please.")
speech.say("you said " + response)
