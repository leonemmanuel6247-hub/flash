import socket
import json
import struct
import os
import shutil
import tempfile
from pathlib import Path
from protocol import pack_header, CHUNK_SIZE
from utils import file_checksum


class FileClient:
    def __init__(self, callback=None):
        self.callback = callback

    def send_file(self, filepath, ip, port):
        temp_zip = None
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                if self.callback:
                    self.callback('erreur', 'Fichier introuvable')
                return

            is_dir = filepath.is_dir()
            if is_dir:
                if self.callback:
                    self.callback('info', f'Compression de {filepath.name}...')
                # Création d'un fichier zip temporaire
                temp_dir = tempfile.mkdtemp()
                zip_path = Path(temp_dir) / f"{filepath.name}.zip"
                shutil.make_archive(str(zip_path.with_suffix('')), 'zip', filepath)
                filepath = zip_path
                temp_zip = temp_dir

            filename = filepath.name
            filesize = filepath.stat().st_size
            checksum = file_checksum(filepath)
            
            if self.callback:
                self.callback('envoi_info', {'filename': filename, 'taille': filesize, 'is_dir': is_dir})
            
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(10.0)
            client.connect((ip, port))
            
            header = pack_header(filename, filesize, checksum, is_dir=is_dir)
            client.sendall(header)
            
            envoye_size = 0
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    client.sendall(chunk)
                    envoye_size += len(chunk)
                    if self.callback:
                        self.callback('progress', envoye_size)
            client.close()
            
            if self.callback:
                self.callback('fini', filename)
        except socket.timeout:
            if self.callback:
                self.callback('erreur', 'Hote introuvable (timeout)')
        except ConnectionRefusedError:
            if self.callback:
                self.callback('erreur', 'Connexion refusee')
        except Exception as e:
            if self.callback:
                self.callback('erreur', str(e))
        finally:
            if temp_zip:
                shutil.rmtree(temp_zip)
