#!/bin/env python
import pycurl
from io import BytesIO
import urllib.parse
import execjs
import re
from html.parser import HTMLParser
import os
import urllib

import pdb

import sys

ESC = '\033['
colours = { 
'none' : "", 
'default' : ESC+"0m", 
'bold' : ESC+"1m", 
'underline' : ESC+"4m", 
'blink' : ESC+"5m", 
'reverse' : ESC+"7m", 
'concealed' : ESC+"8m", 

'black' : ESC+"30m", 
'red' : ESC+"31m", 
'green' : ESC+"32m", 
'yellow' : ESC+"33m", 
'blue' : ESC+"34m", 
'magenta' : ESC+"35m", 
'cyan' : ESC+"36m", 
'white' : ESC+"37m", 

'on_black' : ESC+"40m", 
'on_red' : ESC+"41m", 
'on_green' : ESC+"42m", 
'on_yellow' : ESC+"43m", 
'on_blue' : ESC+"44m", 
'on_magenta' : ESC+"45m", 
'on_cyan' : ESC+"46m", 
'on_white' : ESC+"47m", 

'beep' : "\007", 

# non-standard attributes, supported by some terminals 
'dark' : ESC+"2m", 
'italic' : ESC+"3m", 
'rapidblink' : ESC+"6m", 
'strikethrough': ESC+"9m", 
} 

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def ircify(html):
    #html = html.replace("<B>", colours['bold']).replace("</B>", colours['default'])
    #html = html.replace("<i>", colours['bold']+colours['italic']).replace("</i>", colours['default'])

    begin_regex = re.compile('^[^\0]*?<span class\=\"f\"([^<]+?)?>')
    span_regex = re.compile('<p class\=\"[pq]\"([^<]+?)?>')
    end_regex = re.compile('<p class\=\"o\"([^<]+?)?>[^\0]*$')

    etimologia = re.compile('<span class\=\"a\"([^<]+?)?>')
    ejemplos = re.compile('<span class\=\"h\"([^<]+?)?>')
    enfasis = re.compile('<span class\=\"j\"([^<]+?)?>')
    frases = re.compile('<span class\=\"k\"([^<]+?)?>')
    genero = re.compile('<span class\=\"[dg]\"([^<]+?)?>')

    html = html.replace("</span>", colours['default'])

    html = begin_regex.sub('', html)
    html = span_regex.sub('\n', html)
    html = end_regex.sub('', html)

    html = etimologia.sub(colours['yellow'], html)
    html = ejemplos.sub(colours['cyan'], html)
    html = enfasis.sub(colours['green'], html)
    html = frases.sub(colours['red'], html)
    html = genero.sub(colours['magenta'], html)
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

def the_main(argv):
    for K in range(1, len(argv)):
        palabra = argv[K]
        body = retrieve(palabra)
        body = strip_tags(ircify(body))

        if body.find('No encontrado') != -1:
            print(palabra, end="")
            print(".\nNo encontrado")
        else:
            print(body)

        print('')

def main():
    the_main(sys.argv)

def test():
    with open('response.html', 'r') as Input:
        data = Input.read()
        #pdb.set_trace()
        body = strip_tags(ircify(data))
        print(body)

if  __name__ =='__main__':
    main()
