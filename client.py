import librosa
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
from bluepy.btle import Scanner, DefaultDelegate
import asyncio
import paho.mqtt.client as mqtt

# Configurazione del broker MQTT
broker = "192.168.1.26"  # IP del tuo Raspberry Pi
topic_noise = "sensor/noise"
topic_distance = "sensor/beacon_distance"
topic_alarm = "sensor/beacon_alarm"

# Definire le soglie in dB
soglia_db = 85  # Soglia di sicurezza
livello_db_desiderato = 86  # Livello desiderato per l'audio

# Specificare il percorso del file audio
file_path = r'/home/pi/Scaricati/test1.mp3'
output_path = r'/home/pi/Scaricati/test_adjusted.wav'

# UUID del beacon da rilevare
TARGET_UUID = "c994496a4ef24b428f98e018e6828934"

# Definisci la potenza di trasmissione (Tx Power) del beacon
tx_power = -55  # Modifica questo valore se necessario

def calcola_rms(y):
    return np.sqrt(np.mean(y ** 2))

def livello_rms_db(rms):
    return 20 * np.log10(rms) if rms > 0 else -np.inf

def calcola_livello_picco(y):
    return np.max(np.abs(y))

def livello_picco_db(picco):
    return 20 * np.log10(picco) if picco > 0 else -np.inf

def calcola_durata(y, sr):
    return len(y) / sr

def analizza_spettro(y, sr):
    sp = np.fft.fft(y)
    freqs = np.fft.fftfreq(len(y), 1 / sr)
    sp_abs = np.abs(sp)
    plt.figure(figsize=(10, 6))
    plt.plot(freqs[:len(freqs) // 2], sp_abs[:len(sp_abs) // 2])
    plt.title('Spettro di Frequenza')
    plt.xlabel('Frequenza (Hz)')
    plt.ylabel('Ampiezza')
    plt.show()

def parse_manufacturer_data(manufacturer_data):
    if manufacturer_data.startswith("4c000215"):
        uuid = manufacturer_data[8:40]  # L'UUID inizia dal 9° carattere
        major = manufacturer_data[40:44]  # Major è dopo l'UUID
        minor = manufacturer_data[44:48]  # Minor è dopo Major
        return uuid, major, minor
    else:
        return None, None, None

def calcola_distanza_da_rssi(rssi, tx_power):
    return 10 ** ((tx_power - rssi) / 20.0)

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.beacon_found = False
        self.device_address = None
        self.device_distance = None

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev or isNewData:
            for (adtype, desc, value) in dev.getScanData():
                if desc == "Manufacturer":
                    print(f"Discovered device {dev.addr}, RSSI={dev.rssi} dB")
                    print(f"  Manufacturer = {value}")

                    if value.startswith("4c000215"):
                        uuid, major, minor = parse_manufacturer_data(value)
                        if uuid and uuid == TARGET_UUID:
                            print(f"  Matching UUID: {uuid}")
                            print(f"  Major: {major}")
                            print(f"  Minor: {minor}")
                            print(f"Beacon trovato con indirizzo MAC: {dev.addr}, RSSI: {dev.rssi} dBm")
                            self.beacon_found = True
                            self.device_address = dev.addr
                            self.device_distance = calcola_distanza_da_rssi(dev.rssi, tx_power)

async def rileva_beacon():
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(5.0)  # Scansione per 5 secondi
    delegate = scanner.delegate
    if getattr(delegate, 'beacon_found', False):
        return delegate.device_address, delegate.device_distance
    else:
        return None, None

def publish_mqtt(client, topic, message):
    client.publish(topic, message)
    print(f"Pubblicato su {topic}: {message}")

async def main():
    try:
        # Connessione al broker MQTT
        client = mqtt.Client()
        client.connect(broker, 1883, 60)
        print(f"Connesso al broker MQTT {broker}")

        # Carica il file audio
        y, sr = librosa.load(file_path, sr=None)
        rms = calcola_rms(y)
        rms_db = livello_rms_db(rms)
        picco = calcola_livello_picco(y)
        picco_db = livello_picco_db(picco)
        durata = calcola_durata(y, sr)
        analizza_spettro(y, sr)

        # Se il livello RMS è inferiore a 86 dB, aggiungi rumore per raggiungere 86 dB
        if rms_db < livello_db_desiderato:
            rms_desiderato = 10 ** (livello_db_desiderato / 20)
            differenza_rms = rms_desiderato - rms
            rumore = np.random.normal(0, differenza_rms, len(y))
            y_rumoroso = y + rumore
            rms_db_rumoroso = livello_rms_db(calcola_rms(y_rumoroso))

            # Salva il file modificato usando soundfile
            sf.write(output_path, y_rumoroso, sr)
            print(f"Livello RMS regolato e salvato nel file {output_path} con livello {rms_db_rumoroso:.2f} dB")
            y = y_rumoroso
            rms_db = rms_db_rumoroso
        else:
            print(f"Il livello RMS originale è già sopra la soglia con {rms_db:.2f} dB")

        # Pubblica il livello di rumore sul topic MQTT
        publish_mqtt(client, topic_noise, str(rms_db))

        # Se il livello di rumore supera la soglia, inizia la scansione del beacon
        if rms_db > soglia_db:
            print(f"{output_path} è potenzialmente dannoso con un livello RMS di {rms_db:.2f} dB.")
            print("Inizio scansione continua del beacon...")

            while True:
                mac_address, distanza = await rileva_beacon()
                if mac_address:
                    print(f"Beacon trovato con indirizzo MAC: {mac_address}.")
                    print(f"Distanza stimata dal beacon: {distanza:.2f} metri.")
                    
                    # Pubblica la distanza sul topic MQTT
                    publish_mqtt(client, topic_distance, str(distanza))
                    
                    if distanza <= 1.0:
                        alarm_message = "Allarme: Il beacon è troppo vicino!"
                        print(alarm_message)
                        publish_mqtt(client, topic_alarm, alarm_message)
                    else:
                        print("Il beacon si trova a una distanza sicura.")
                else:
                    print("Beacon non trovato.")
                
                await asyncio.sleep(2)  # Attendi 2 secondi prima della prossima scansione

        else:
            print(f"{output_path} è sicuro con un livello RMS di {rms_db:.2f} dB.")
        
        print(f"Livello di picco: {picco_db:.2f} dB")
        print(f"Durata del segnale: {durata:.2f} secondi")

    except FileNotFoundError:
        print(f"File non trovato: {file_path}")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")
    finally:
        client.disconnect()

# Esegui il codice asincrono
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nScansione interrotta dall'utente.")
