#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# TODO: сделать возможность вставлять вместо url путь к папке на диске,
# скрипт не видит http и считает что это папка, скачивает из неё файлы и
# нумерует.
# - добавить уже json в конфиге и выложить на гитхаб
import os
import datetime
import subprocess
from mutagen.mp3 import MP3
from xml.etree import ElementTree as ET

print('0. Чтение dlconfig')
config = open("dlconfig", "r")
clines = [line.rstrip('\n') for line in config]
# TODO: добавить в конфиг и перевести конфиг в JSON
domain = 'http://someaddr.net'
prefixpath = '/var/www/html'
episodePrefix = 'episode_'

print('1. Бежим по каждым двум строкам из dlconfig')
for ln in range(len(clines)):
    if ((ln+1)%2)==0:
        continue
    downlink = clines[ln]
    domainpath = clines[ln+1].strip('/')
    storpath = prefixpath + '/' + (domainpath)
#    epName = 'episode' + epNum + '.mp3'
    symlinks = storpath + '/symlinks'

    print('2. Создание папки для mp3 и для мягких ссылок')
    if os.path.isdir(storpath)!=True:
        os.mkdir(storpath)
    if os.path.isdir(symlinks)!=True:
        os.mkdir(symlinks)

    print('3. Cкачивание файлов')
# TODO: требуется sudo! :(
# subprocess.call(["youtube-dl", "-U", "--verbose"])
    downexec = "youtube-dl -q -o '"+storpath+"/%(playlist_index)s-%(title)s-%(id)s.%(ext)s' -x --audio-format \"mp3\" '"+downlink+"'" # , "--verbose"]

#    downexec = ["youtube-dl", "-q", "-o", "'"+storpath+"/%(playlist_index)s-%(title)s-%(id)s.%(ext)s'", "-x", "--audio-format \"mp3\"", "'"+downlink+"'"] # , "--verbose"]
#    downexec = ["youtube-dl", "-q -o '"+storpath+"/%(playlist_index)s-%(title)s-%(id)s.%(ext)s' -x --audio-format \"mp3\" '"+downlink+"'"]
    print(downexec)
    subprocess.call(downexec, shell=True)
#    subprocess.call(downexec)

    print('4. Создание мягких ссылок на файлы')
# NOTICE: директория с мягкими ссылками не очищается полностью, удаляются только файлы с совпавшими номерами
    mp3s = os.listdir(storpath)
    for m in range(len(mp3s)):
        mp3file = mp3s[m]
        fnameext = os.path.splitext(mp3file)
        if fnameext[1] != '.mp3':
            continue
        afterNum = mp3file.find('-')
        episodeNumber = mp3file[0:afterNum].lstrip('0')
        epName = episodePrefix + episodeNumber + '.mp3'
        symName = symlinks
        mp3path = storpath + '/' + mp3file
        sympath = symlinks + '/' + epName
        if os.path.islink(sympath):
            os.remove(sympath)
        os.symlink(mp3path, sympath)
        #print mp3path
        #print sympath
        #print "- -  -   -    -"

    print('5. Создание xml')
    rsspath = storpath + '/rss.xml'

    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
    ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    xml_tree = ET.parse('./rss-template.xml')
    xml_root = xml_tree.getroot()

    print('6. Заголовок xml')
    xml_title = next(xml_root.iter('title'))
    xml_link = next(xml_root.iter('link'))
    xml_title.text = downlink
    xml_link.text = downlink

    print('7. Выпуски')
    # print('symlinks = ') + symlinks
    syms = os.listdir(symlinks)

    # TODO: сделать сортировку файлов-ссылок по номеру эпизода! Т.е. сортировку массива строк.

    numsArr = []
    for s in range(0, len(syms)):
        symfile = syms[s]
        if symfile[0:8]!="episode_":
            continue
        numsArr.append(int(symfile[8:-4]))

    numsArr = sorted(numsArr)
    #print numsArr

    dateVal = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S")

    xml_channel = xml_root.find('channel')
    xml_item = xml_channel.find('item')
    xml_channel.remove(xml_item)

    for s in range(0, len(numsArr)):
        symname = episodePrefix + str(numsArr[s]) + '.mp3'
        fullpath = symlinks + '/' + symname
        audio = MP3(fullpath)
        filesize = os.path.getsize(fullpath)
        realpath = os.path.realpath(fullpath)
# Нужно как-то получить, куда указывает ссылка

        xml_item = ET.Element('item')
        subE = ET.SubElement(xml_item, 'title')
        subE.text = realpath[len(storpath)+1:-4]
        subE = ET.SubElement(xml_item, 'pubDate')
        subE.text = dateVal
        subE = ET.SubElement(xml_item, 'guid')
        subE.text = str(s + 1)
        subE = ET.SubElement(xml_item, 'author')
        subE.text = 'rssgen.py'
        subE = ET.SubElement(xml_item, 'enclosure')
        subE.set('type', 'audio/mpeg')
        subE.set('length', str(filesize))
        subE.set('url', '{}/{}/symlinks/{}'.format(domain, domainpath, symname))

        xml_channel.append(xml_item)

    print('8. Создание rss.xml')
    xml_tree.write(rsspath,
                   xml_declaration=True, encoding='UTF-8', method='xml')
