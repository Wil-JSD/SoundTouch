#The Bose SoundTouch Controller app and the json_server software is developed by JSD\n\n'
#
#MIT License
#
#Copyright (c) [2026] [JSD], JSD@kpnmail.nl
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
#
from flask import Flask, Response, request, send_from_directory, redirect, url_for, jsonify
import requests
import json
import glob
import os
from pathlib import Path

app = Flask(__name__)

# HOST = "192.168.2.24"
# HOST = "localhost"
HOST = "raspberry-pi"
PORT = 8081

# ---- Load JSON stations ----
STATIONS = {}

def load_station_json():
# Path("stations") werkt op beide systemen
    for file_path in Path("stations").glob("*.json"):
        with open(file_path, "r") as f:
            data = json.load(f)

        name = file_path.stem
        # We slaan nu een dictionary op met de stream én het bestandspad
        STATIONS[name] = {
            "name": data["name"],
            "stream": data["audio"]["streamUrl"],
            "path": file_path.as_posix()  # Dit geeft "stations/radioserver.json"
        }      
load_station_json()

# ---- Refresh ----
@app.route("/refresh")
def refresh():
    global STATIONS  # Zorg dat we de STATIONS buiten de functie aanpassen
    STATIONS.clear()    # Maak de lijst leeg
    load_station_json()
    
    # Stuur de browser direct door naar de /opml route
    return redirect(url_for('opml'))

# ---- OPML ----
@app.route("/opml")
def opml():
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<opml version="1.0">',
        '<body>'
    ]
    for name, info in STATIONS.items():
        # Gebruik info["path"] in plaats van de stationsnaam
        xml.append(
            f'<outline name="{info["name"]}"  key="{name}" '
            f'json="http://{HOST}:{PORT}/{info["path"]}" '
            f'streamurl="{info["stream"]}" />'
        )

    xml.append('</body></opml>')
    return Response("\n".join(xml), content_type="text/xml")

# ---- Serve station JSON ----
@app.route("/stations/<name>.json", methods=['GET'])
def get_station_json(name):
    return send_from_directory("stations", f"{name}.json")

# ---- Write station JSON ----
@app.route("/stations/<name>.json", methods=['POST'])
def create_station(name):
    data = request.json
    filepath = os.path.join("stations", f"{name}.json")

    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return jsonify({"message": "File created", "path": filepath}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- Delete station JSON ----
@app.route("/stations/<name>.json", methods=["DELETE"])
def delete_station(name):
    filepath = os.path.join("stations", f"{name}.json")

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"status": "success", "message": f"{name}.json verwijderd"}), 200
        else:
            return jsonify({"status": "error", "message": "Bestand niet gevonden"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

## ---- Serve JSON files for preset locations ----
#from flask import send_from_directory

#@app.route('/Documents/BOSE/API/cloud/stations/<filename>')
#def serve_cloud_file(filename):
#    return send_from_directory('Documents/BOSE/API/cloud/stations', filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
