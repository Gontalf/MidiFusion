from flask import Flask, request, send_file
import os
import random
import string
import mido
from mido import MidiFile, MidiTrack, Message

app = Flask(__name__)

def generate_random_filename():
    """Genera un nombre de archivo aleatorio."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + ".mid"

def merge_midi_files(files):
    """Combina archivos MIDI en orden alfabético, agregando cada uno después del anterior sin mezclar pistas."""
    merged_midi = MidiFile()
    merged_track = MidiTrack()
    merged_midi.tracks.append(merged_track)

    files.sort()  # Ordenar archivos alfabéticamente
    
    current_time = 0  # Tiempo acumulado para cada archivo

    for file in files:
        midi = MidiFile(file)

        for track in midi.tracks:
            new_track = MidiTrack()
            new_track.append(mido.MetaMessage('track_name', name=os.path.basename(file)))
            
            for msg in track:
                if not msg.is_meta:  # Ignorar mensajes de metadatos
                    msg.time += current_time  # Desplazar el tiempo de las notas
                    new_track.append(msg)

            merged_midi.tracks.append(new_track)

        # Ajustar el tiempo total acumulado al final del archivo
        for msg in midi.tracks[0]:  # Asumimos que la primera pista tiene la información de tempo
            if msg.type == 'note_on' or msg.type == 'note_off':
                current_time += msg.time

    output_filename = generate_random_filename()
    merged_midi.save(output_filename)
    return output_filename

@app.route('/upload', methods=['POST'])
def upload_files():
    """Recibe archivos MIDI, los fusiona y devuelve el archivo combinado."""
    uploaded_files = request.files.getlist("files")
    if not uploaded_files:
        return "No se han subido archivos", 400

    file_paths = []
    os.makedirs("temp", exist_ok=True)  # Crear carpeta temporal si no existe

    for file in uploaded_files:
        file_path = os.path.join("temp", file.filename)
        file.save(file_path)
        file_paths.append(file_path)

    # Fusionamos los archivos
    merged_filename = merge_midi_files(file_paths)

    # Limpiar archivos temporales
    for file in file_paths:
        os.remove(file)

    return send_file(merged_filename, as_attachment=True)

if __name__ == '__main__':
    from flask_cors import CORS
CORS(app)
    app.run(debug=True, host="127.0.0.1", port=5000)

