CARICARE GLI AUDIO 
# Per vedere la Web Page [Progetto WoT - Palumbo & Pierri](https://unisalento-idalab-iotcourse-2023-2024.github.io/wot-project-presentation-PalumboPierri/)

# Monitoraggio Audio e Distanza Beacon

## Descrizione del Progetto

Questo progetto combina l'analisi del rumore ambientale con il monitoraggio della distanza di un beacon tramite Bluetooth Low Energy (BLE) utilizzando un Raspberry Pi. L'obiettivo è monitorare il livello sonoro di un file audio e rilevare la distanza di un beacon per avvisare quando i livelli di rumore superano una soglia potenzialmente dannosa e il beacon si trova troppo vicino al dispositivo.

### Funzionalità Principali:
1. **Analisi Audio**:
   - Il file audio viene caricato e analizzato in termini di livello RMS (Root Mean Square), livello di picco e spettro di frequenza.
   - Se il livello RMS è inferiore a una soglia desiderata, viene aggiunto del rumore per portarlo al livello desiderato (86 dB).
   - Se il livello di rumore supera la soglia di sicurezza (85 dB), viene attivato il monitoraggio del beacon BLE.

2. **Monitoraggio Distanza Beacon**:
   - Scansione continua dei beacon BLE circostanti per rilevare un beacon specifico (identificato tramite UUID).
   - Quando il beacon viene rilevato, viene calcolata la distanza stimata in base al valore RSSI.
   - Se il beacon si trova a meno di 1 metro, viene inviato un allarme.
   - La potenza di trasmissione può essere variata in base alla distanza del beacon, aumentandola per distanze maggiori e diminuendola nelle vicinanze

3. **Integrazione con MQTT**:
   - Pubblicazione dei dati di livello di rumore e distanza del beacon su un broker MQTT per il monitoraggio remoto.
   - Pubblicazione di un allarme quando il lavoratore (beacon) si trova troppo vicino al dispositivo.

---

## Dipendenze e tips il funzionamento 

Assicurarsi di avere installato le seguenti librerie:

- **librosa**: per il caricamento e l'analisi dei file audio.
- **numpy**: per i calcoli numerici.
- **matplotlib**: per visualizzare lo spettro di frequenza.
- **soundfile**: per salvare i file audio modificati.
- **bluepy**: per la scansione BLE dei beacon.
- **paho-mqtt**: per la pubblicazione dei dati tramite MQTT.
- **asyncio**: per la gestione asincrona delle operazioni (scansione beacon).

È possibile installare queste dipendenze con:


```bash
pip install librosa numpy matplotlib soundfile bluepy paho-mqtt
```
---

Inoltre per far funzionare il codice è necessario cambiare il path della variabile file_path e output_path con il path necessario per drill.mp3
