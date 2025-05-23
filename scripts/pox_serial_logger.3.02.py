#!/usr/bin/env python3
import serial
import configparser
import os
import time
import datetime
import json
import re
import argparse
import logging
from collections import defaultdict

# Globale Zustandsverwaltung für CSS-Farben
css_states = defaultdict(lambda: {'state': 'g', 'since': None})

def load_config(config_path='config.ini'):
    # Konfigurationsdatei laden
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def open_serial(port, baudrate):
    # Serielle Verbindung öffnen und bei Fehlern erneut versuchen
    while True:
        try:
            ser = serial.Serial(port, baudrate, timeout=1)
            logging.info(f"[INFO] Serielle Verbindung geöffnet: {port} @ {baudrate} Baud")
            return ser
        except serial.SerialException as e:
            logging.warning(f"[WARN] Serielle Verbindung fehlgeschlagen: {e}. Neuer Versuch in 5 Sekunden...")
            time.sleep(5)

def ensure_output_directory(filepath):
    # Sicherstellen, dass das Ausgabeverzeichnis existiert
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def strip_leading_zeros(value):
    # Führende Nullen aus numerischen Werten entfernen
    return str(int(float(value))) if value.replace('.', '', 1).isdigit() else value

def extract_value(key, line):
    # Wert für einen bestimmten Schlüssel aus einer Zeile extrahieren
    match = re.search(rf'\b{key}=([^\s]+)', line)
    return match.group(1) if match else ''

def update_css_state(label, active, now, config):
    # CSS-Zustand basierend auf Alarm- und Ausnahmebits aktualisieren
    state_info = css_states[label]
    if active:
        css_states[label] = {'state': 'r', 'since': now}
        return 'r'
    else:
        if state_info['state'] == 'r':
            css_states[label] = {'state': 'o', 'since': now}
            return 'o'
        elapsed = (now - state_info['since']).total_seconds() if state_info['since'] else 0
        if state_info['state'] == 'o' and elapsed >= config['time2y']:
            css_states[label]['state'] = 'y'
            css_states[label]['since'] = now
            return 'y'
        elif state_info['state'] == 'y' and elapsed >= config['time2g']:
            css_states[label]['state'] = 'g'
            css_states[label]['since'] = now
            return 'g'
        else:
            return state_info['state']

def generate_css_fields(alarm_hex, exc_hex, config):
    # CSS-Felder basierend auf Alarm- und Ausnahmebits generieren
    css = {}
    try:
        alarm_bits = int(alarm_hex, 16)
    except ValueError:
        alarm_bits = 0
    try:
        exc_bits = int(exc_hex, 16)
    except ValueError:
        exc_bits = 0
    now = datetime.datetime.now()
    for i in range(1, 13):
        label = f'A{i}'
        bit_set = (alarm_bits & (1 << (i - 1))) != 0
        css[label] = update_css_state(label, bit_set, now, config)
    for i in range(1, 13):
        label = f'E{i}'
        bit_set = (exc_bits & (1 << (i - 1))) != 0
        css[label] = update_css_state(label, bit_set, now, config)
    return css

def write_json(output_path, spo2, bpm, pi, alarm, exc, config):
    # JSON-Datei mit den Messwerten schreiben
    json_path = os.path.join(os.path.dirname(output_path), "pox.json")
    now = datetime.datetime.now()
    timestamp = now.strftime('%d.%m.%Y %H:%M:%S')
    json_data = {
        "SampleDate": timestamp,
        "SPO2": strip_leading_zeros(spo2.replace('%', '')),
        "BPM": strip_leading_zeros(bpm),
        "PI": strip_leading_zeros(pi),
        "ALARM": alarm,
        "EXC": exc,
        "sleep": "",
        "CSS": generate_css_fields(alarm, exc, config)
    }
    with open(json_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=2)

def parse_config_times(config):
    # Zeitkonfigurationen aus der Konfigurationsdatei lesen
    return {
        'time2o': config.getint('settings', 'time2o', fallback=10),
        'time2y': config.getint('settings', 'time2y', fallback=60),
        'time2g': config.getint('settings', 'time2g', fallback=300),
    }

def setup_logging(debug, logfile_path):
    # Logging-Konfiguration einrichten
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(logfile_path, mode='a')
        ]
    )

def main():
    # Hauptfunktion
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Aktiviere Debug-Modus')
    args = parser.parse_args()

    config_raw = load_config()
    config_times = parse_config_times(config_raw)
    debug = args.debug

    logfile_path = config_raw['output'].get('logfile', '/var/log/pox_logger.log')
    setup_logging(debug, logfile_path)

    port = config_raw['serial']['port']
    baudrate = int(config_raw['serial']['baudrate'])
    output_path = config_raw['output']['filepath']

    ensure_output_directory(output_path)

    while True:
        ser = open_serial(port, baudrate)
        try:
            with ser, open(output_path, 'a', buffering=1) as outfile:
                logging.info(f"[INFO] Schreibe Daten nach: {output_path}")
                while True:
                    line = ser.readline().decode('ascii', errors='ignore').strip()
                    if line:
                        timestamp = datetime.datetime.now().isoformat()
                        output_line = f"{timestamp} {line}"
                        outfile.write(output_line + '\n')

                        spo2 = extract_value('SPO2', line)
                        bpm = extract_value('BPM', line)
                        pi = extract_value('PI', line)
                        alarm = extract_value('ALARM', line)
                        exc = extract_value('EXC', line)

                        write_json(output_path, spo2, bpm, pi, alarm, exc, config_times)

                        logging.debug(f"[DATA] {output_line}")
        except serial.SerialException as e:
            logging.error(f"[ERROR] Verbindungsfehler: {e}. Neuer Versuch...")
            time.sleep(2)
        except KeyboardInterrupt:
            logging.info("[INFO] Beendet durch Benutzer")
            break

if __name__ == "__main__":
    main()
