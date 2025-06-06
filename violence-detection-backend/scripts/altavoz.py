import pyttsx3

engine = pyttsx3.init()
engine.say("Alerta: se ha detectado una pelea en el pasillo principal")
engine.runAndWait()

print("Alerta: se ha detectado una pelea en el pasillo principal")