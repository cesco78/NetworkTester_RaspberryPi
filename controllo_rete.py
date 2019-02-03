#!/usr/bin/env python

# questo programma fa parte del progetto dell'analizzatore di rete per non tecnici
# che si puo' trovare all'indirizzo http://www.iltucci.com/blog/2019/01/30/un-semplice-analizzatore-della-rete-su-raspberry-pi-(per-noob)/
#
# Sviluppato da Francesco Tucci (http://www.iltucci.com)
# Versione 1.0 del 03/02/2019
#
# Parte del codice e' presa dai programi di esempio di Pimoroni (quelli che si instalano con l'installazione delle librerie)
# Rilasciato con licenza GPL (Puoi utilizzarlo e modificalo come ti pare, ma devi indicare da dove lo hai preso)

import time
import signal

# queste librerie servono per gestire il display e la grafica
from gfxhat import touch, lcd, backlight, fonts
from PIL import Image, ImageFont, ImageDraw

# questa serve per sapere l'IP e il gateway del raspberry
import netifaces

# libreria per chiamare i programmi del sistema operativo
import os

# inizializza variabili e opzioni
width, height = lcd.dimensions()
image = Image.new('P', (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.truetype(fonts.BitbuntuFull, 10)

# queste informazioni sono invece relativ ai test che si vogliono fare
# io per controllare se c'e' Internet faccio ping all'indirizzo dei DNS di Google 8.8.8.8
# ma si puo' mettere un IP qualunque in base alle proprie esigenze
#
# per controllare invece la VPN serve mettere un IP della sede centrale
# in modo da capire se e' raggiungibile e con che latenza
indirizzo_internet = "8.8.8.8"
indirizzo_vpn = "192.168.0.0"

# imposta il colore della retroilluminazione del display
def set_backlight(r, g, b):
    backlight.set_all(r, g, b)
    backlight.show()

# procedura che disegna sul display cosa c'e' nel buffer
def disegna():
    for x in range(128):
        for y in range(64):
            pixel = image.getpixel((x, y))
            lcd.set_pixel(x, y, pixel)

# spegne e cancella il display
def cleanup():
    backlight.set_all(0, 0, 0)
    backlight.show()
    lcd.clear()
    lcd.show()

# svuota il buffer dello schermo disegnando un rettangolo
# pieno di punti settati a zero
def cancella_schermo():
    draw.rectangle((0,0,width, height), fill = 0)
    lcd.show()

# fa il ping a un indirizzo, restituisce:
#  0 se il ping va a buon fine
#  1 se il ping fallisce
def controlla_ping(indirizzo):
    p = os.system("ping -c 1 " + indirizzo)
    return p

# restituice la latenza media verso l'IP indicato
def controlla_latenza(indirizzo):
    l = os.popen("ping -c 5 " + indirizzo +" | grep rtt | awk -F '/' '{print $5}'").read()
    return l

# restituisce lo speedtest
def speedtest():
    risultato = os.popen("speedtest-cli --simple | awk '{print $2}'").read()
    return risultato.splitlines()

# restituisce l'operatore della connettivita'
# il sito ipinfo.io e' davvero interessante
def gestore_internet():
    gestore = os.popen("curl ipinfo.io/org").read()
    return gestore

    


### da qui inizia l'analisi ###
###############################

# messaggio di benvenuto su sfondo bianco
set_backlight(255,255,255)            
draw.text((0, 0), 'Test rete sede remota', 1, font)
draw.text((0, 10), '*********************', 1, font)
draw.text((0, 20), 'Attendere il termine', 1, font)
draw.text((0, 30), '(LCD verde o rosso)', 1, font)
draw.text((0, 40), 'e fare una foto.', 1, font)
draw.text((50, 50), 'Grazie!', 1, font)
disegna()
lcd.show()

# incrementa di uno per ogni problema
# se alla fine e' maggiore di zero il display diventa rosso
problemi = 0
gws_errore = 0

# aspetta 15'' e poi cancella il display (15'' cosi' aspetta il DHCP)
time.sleep(15)
cancella_schermo()

# mette lo schermo a blu mentre lavora
set_backlight(0,0,255)

# recupera l'indirizzo IP della scheda eth0
# e lo scrive a video
try:
    addrs = netifaces.ifaddresses('eth0')
    indirizzo_ip = addrs[netifaces.AF_INET][0]['addr']
    draw.text((0, 0), 'IP:' + indirizzo_ip, 1, font)
except:
    draw.text((0, 0), 'IP: ERRORE', 1, font)
    problemi = problemi + 1
# aggiorna il display
disegna()
lcd.show()

# recupera il default gateway e lo scrive a video
try:
    gws = netifaces.gateways()
    gateway = gws['default'][netifaces.AF_INET][0]
    draw.text((0, 10), 'GW:' + gateway, 1, font)
except:
    draw.text((0, 10), 'GW: ERRORE', 1, font)
    problemi = problemi + 1
    gws_errore = 1
# aggiorna il display
disegna()
lcd.show()

# verifica che Internet sia connesso con un ping
connesso_internet = controlla_ping(indirizzo_internet)
if connesso_internet == 0:
    draw.text((0, 20), 'Internet OK', 1, font)
else:
    problemi = problemi + 1
    draw.text((0, 20), 'Internet NO', 1, font)
# aggiorna il display
disegna()
lcd.show()
    
# verifica che la VPN sia connessa con un ping a un server all'interno della VPN
connesso_vpn = controlla_ping(indirizzo_vpn)
if connesso_vpn == 0:
    draw.text((0, 30), 'VPN OK', 1, font)
else:
    problemi = problemi + 1
    draw.text((0, 30), 'VPN NO', 1, font)
# aggiorna il display
disegna()
lcd.show()
    
# controlla la latenza verso il gateway
if gws_errore == 0:
    latenza_gateway = controlla_latenza(gateway)
    draw.text((100, 10), str(latenza_gateway), 1, font)
else:
    draw.text((100, 10), "--", 1, font)
# aggiorna il display
disegna()
lcd.show()

# controlla la latenza verso Internet solo se Internet va
if connesso_internet == 0:
    latenza_internet = controlla_latenza(indirizzo_internet)
    draw.text((100, 20), str(latenza_internet), 1, font)
else:
    draw.text((100, 20), "--", 1, font)
# aggiorna il display
disegna()
lcd.show()

# controlla la latenza verso la VPN solo se la VPN va
if connesso_vpn == 0:
    latenza_vpn = controlla_latenza(indirizzo_vpn)
    draw.text((100, 30), str(latenza_vpn), 1, font)
else:
    draw.text((100, 30), "--", 1, font)
# aggiorna il display
disegna()
lcd.show()

# se internet non e' connesso salta tutto il test di velocita'
# per fare il test della velocita' uso il classico speedtest.net
# che ha un bel client da installare su Linux
if connesso_internet == 0:
    # scrive il testo "speed" per indicare che sta calcolando
    draw.text((0, 40), "Test velocita'...", 1, font)
    # aggiorna il display
    disegna()
    lcd.show()
    
    # fa lo speed test
    test_speed = speedtest()
    draw.text((0, 40), "Test velocita'...", 0, font) # scrivendo lo stesso testo, ma con il colore a zero, lo cancello.
    draw.text((0, 40), "Speed:", 1, font)
    draw.text((40, 40), test_speed[1], 1, font)
    draw.text((84, 40), test_speed[2], 1, font)
    # aggiorna il display
    disegna()
    lcd.show()
    
    # recupera il gestore Internetr
    isp = gestore_internet()
    print isp
    draw.text((0, 50), isp, 1, font)
    # aggiorna il display
    disegna()
    lcd.show()
else:
    draw.text((0, 40), "NESSUN TEST", 1, font)
    # aggiorna il display
    disegna()
    lcd.show()

# fine dei test, lo sfondo diventa verde se tutto ok
# rosso se ci sono problemi
if problemi == 0:
    set_backlight(0,255,0)
else:
    set_backlight(255,0,0)


# questa cosa e' usata durante lo sviluppo.
# se non si fa nulla il display resta cosi' come ha finito di lavorare
# se si interrompe con Ctrl+C il display viene spento e cancellato.
try:
    signal.pause()
except KeyboardInterrupt:
    cleanup()
