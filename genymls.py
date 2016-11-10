import os
import datetime
from mutagen.mp3 import MP3

guidCounter = 0
dateVal = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
path = "/var/www/html/pod/"
files = os.listdir(path)
for f in files:
	if f[-3:] != 'mp3':
		continue
	fullpath = path + f
	guidCounter = guidCounter + 1
	outputFile = open("ymls/episode-" + str(guidCounter) + ".yml", "w")
	audio = MP3(fullpath)
	fileSize = os.path.getsize(fullpath)
	newname = 'ep' + str(guidCounter) + '.mp3'
	outputStr = "---\n\n"
	outputStr+= "title: " + f + "\n"
	outputStr+= "author: Someone from outer internets\n\n"
	outputStr+= "subtitle: " + f + "\n\n"
        outputStr+= "summary: Another episode\n\n"
        outputStr+= "#image:\n\n"
        outputStr+= "guid: " + str(guidCounter) + "\n\n"
        outputStr+= "pubDate: " + dateVal + " YEKT\n\n"
        outputStr+= "enclosureUrl: http://someaddr.net/pod/" + newname + "\n\n"
        outputStr+= "enclosureLength: " + str(fileSize) + "\n\n"
        outputStr+= "enclosureType: audio/mpeg\n\n"
        outputStr+= "duration: " + str(audio.info.length) + "\n\n"
        outputStr+= "---"
	outputFile.write(outputStr)
	outputFile.close()
	os.rename(fullpath, path + newname)
