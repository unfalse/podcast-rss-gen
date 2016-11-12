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
import json

print('0. Чтение config.json')
with open('config.json') as f:
    config = json.load(f)
domain = config['domain'] if config.get('domain', False) else 'http://someaddr.net'
prefixpath = config['prefixpath'] if config.get('prefixpath', False) else '~/rssgen'
prefixpath = os.path.expanduser(prefixpath)
episodePrefix = config['episodePrefix'] if config.get('episodePrefix', False) else 'episode_'
clines = config['dl_list']

print('1. Бежим по каждым двум строкам из dlconfig')
for ln in clines:
    downlink = ln['downlink']
    domainpath = ln['domainpath']
    storpath = prefixpath + '/' + domainpath # /var/www/html/pod/blabla
#    epName = 'episode' + epNum + '.mp3'
    symlinks = storpath + '/symlinks'

    print('2. Создание папки для mp3 и для мягких ссылок')
    if not os.path.isdir(storpath):
        os.makedirs(storpath)
    if not os.path.isdir(symlinks):
        os.makedirs(symlinks)

    print('3. Cкачивание файлов')
# subprocess.call(["youtube-dl", "-U", "--verbose"])
#     downexec = "youtube-dl -q -o '"+storpath+"/%(playlist_index)s-%(title)s-%(id)s.%(ext)s' -x --audio-format \"mp3\" '"+downlink+"'" # , "--verbose"]
    downexec = "youtube-dl -q -o '{}/%(playlist_index)s-%(title)s-%(id)s.%(ext)s' -x --audio-format \"mp3\" '{}'".\
        format(storpath, downlink)

#    downexec = ["youtube-dl", "-q", "-o", "'"+storpath+"/%(playlist_index)s-%(title)s-%(id)s.%(ext)s'", "-x", "--audio-format \"mp3\"", "'"+downlink+"'"] # , "--verbose"]
#    downexec = ["youtube-dl", "-q -o '"+storpath+"/%(playlist_index)s-%(title)s-%(id)s.%(ext)s' -x --audio-format \"mp3\" '"+downlink+"'"]
    print(downexec)
    subprocess.call(downexec, shell=True)
#    subprocess.call(downexec)

    print('4. Создание мягких ссылок на файлы')
# NOTICE: директория с мягкими ссылками не очищается полностью, удаляются только файлы с совпавшими номерами
    mp3s = os.listdir(storpath)
    for mp3file in mp3s:
        if not mp3file.endswith('.mp3'):
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
    for symfile in syms:
        if not symfile.startswith('episode_'):
            continue
        numsArr.append(int(symfile[8:-4]))

    numsArr = sorted(numsArr)
    #print numsArr

    dateVal = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S")

    xml_channel = xml_root.find('channel')
    xml_item = xml_channel.find('item')
    xml_channel.remove(xml_item)

    for s in numsArr:
        symname = '{}{}.mp3'.format(episodePrefix, s)
        fullpath = symlinks + '/' + symname
        audio = MP3(fullpath)
        filesize = os.path.getsize(fullpath)
        realpath = os.path.realpath(fullpath)
# Нужно как-то получить, куда указывает ссылка

        xml_item = ET.Element('item')
        sub = ET.SubElement(xml_item, 'title')
        sub.text = realpath[len(storpath)+1:-4]
        sub = ET.SubElement(xml_item, 'pubDate')
        sub.text = dateVal
        sub = ET.SubElement(xml_item, 'guid')
        sub.text = str(s + 1)
        sub = ET.SubElement(xml_item, 'author')
        sub.text = 'rssgen.py'
        sub = ET.SubElement(xml_item, 'enclosure')
        sub.set('type', 'audio/mpeg')
        sub.set('length', str(filesize))
        sub.set('url', '{}/{}/symlinks/{}'.format(domain, domainpath, symname))

        xml_channel.append(xml_item)

    print('8. Создание rss.xml')
    xml_tree.write(rsspath,
                   xml_declaration=True, encoding='UTF-8', method='xml')
