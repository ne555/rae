#!/bin/env python
import pycurl
from io import BytesIO
import urllib.parse
import execjs
import re
from html.parser import HTMLParser
import os
import urllib

import sys

def ircify(html):
    begin_regex = re.compile('^[^\0]*<span class\=\"f\"([^<]+?)?>')
    span_regex = re.compile('<p class\=\"[pq]\"([^<]+?)?>')
    end_regex = re.compile('<p class\=\"o\"([^<]+?)?>[^\0]*$')

    html = begin_regex.sub('', html)
    html = span_regex.sub('\n', html)
    html = end_regex.sub('', html)
    return html

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)
    def handle_entityref(self, name):
        self.fed.append('&%s;' % name)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def retrieve(palabra):
    buffer = BytesIO()
    #change to use `requests'
    c = pycurl.Curl()
    #c.setopt(c.URL, 'http://dle.rae.es/?w='+palabra) #actualizado
    address = 'http://lema.rae.es/drae/srv/search?'
    palabra_enc = urllib.parse.urlencode({'key':palabra})
    c.setopt(c.URL, address+palabra_enc)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()

    body = buffer.getvalue()
    l = body.decode().split("<script>")[1].split("</script>")[1].replace('<script type="text/javascript">', '').replace('document.forms[0].elements[1].value=', 'return ')
    ctx = execjs.compile(l)
    chall = ctx.call("challenge")
    pdata = "&".join(body.decode().split("<body")[1].replace("/>", "\n").split("\n")[1:-1]).replace('<input type="hidden" name="', '').replace('" value="', '=').replace('"','').replace('TS014dfc77_cr=', 'TS014dfc77_cr=' + urllib.parse.quote_plus(chall))

    buffer = BytesIO()

    c = pycurl.Curl()
    c.setopt(c.URL, address+palabra_enc)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(pycurl.HTTPHEADER, ["Referer: http://lema.rae.es/drae/srv/search?key=hola",
    "Cache-Control: max-age=0",
    "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Origin: http://lema.rae.es",
    "User-Agent: Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/39.0.2171.65 Chrome/39.0.2171.65 Safari/537.36"
    ])
    c.setopt(c.POSTFIELDS, pdata)
    c.perform()
    body = buffer.getvalue().decode()
    return body

def main():
    for K in range(1, len(sys.argv)):
        palabra = sys.argv[K]
        print(palabra, end="")
        body = strip_tags(ircify(retrieve(palabra)))

        if body.find('No encontrado') != -1:
            print(".\nNo encontrado")
        else:
            print(body)

        print('')

if  __name__ =='__main__':
    main()
