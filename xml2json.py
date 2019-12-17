#!/bin/python3
# coding=utf-8
import json
import xml.etree.ElementTree as ET

def xml2json(node):
    xdic = {}
    for item in node:
        if len(item) > 0:
            value = xml2json(item)
        else:
            value = item.text
        if item.tag in xdic:
            if type(xdic[item.tag]) != list:
                xdic[item.tag] = [xdic[item.tag], value]
            else:
                xdic[item.tag].append(value)
        else:
            xdic[item.tag] = value
    return xdic

# with open('feed.xml', 'r', encoding='utf8') as f:
    # root = ET.fromstring(f.read())
root = ET.parse('feed.xml').getroot()
xdic = {root.tag: xml2json(root)}

#xdic['contest']['team'].sort(key='id')
#xdic['contest']['clar'].sort(key='id')
#xdic['contest']['run'].sort(key='id')
#xdic['contest']['testcase'].sort(key='id')

# print(json.dumps(xdic, indent=2, separators=(',', ': '), ensure_ascii=False))

xdic['contest'].pop('language')
xdic['contest'].pop('judgement')
#xdic['contest'].pop('region')
xdic['contest'].pop('clar')
xdic['contest'].pop('testcase')
#xdic['contest'].pop('finalized')

with open('feed.json', 'w', encoding='utf8') as f:
    json.dump(xdic, f, indent=2, separators=(',', ': '), ensure_ascii=False)
    # json.dump(xdic, f, ensure_ascii=False)