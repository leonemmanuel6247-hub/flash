import socket
import threading
import os
import hashlib
import struct
import shutil
from pathlib import Path
from protocol import unpack_header, recv_all, CHUNK_SIZE

RECEIVE_DIR = Path.home() / 'Recus'


class FileServer:
    def __init__(self, port, callback=None):
        self.port = port
        self.callback = callback
        self.running = False
        self.server = None
        self.thread = None

    def start(self):
        RECEIVE_DIR.mkdir(parents=True, exist_ok=True)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', self.port))
        self.server.listen(5)
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if self.callback:
            self.callback('serveur_demarre')

    def stop(self):
        self.running = False
        if self.server:
            self.server.close()
        if self.callback:
            self.callback('serveur_arrete')

    def _run(self):
        while self.running:
            try:
                self.server.settimeout(1.0)
                conn, addr = self.server.accept()
                threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, conn, addr):
        filepath = None
        try:
            if self.callback:
                self.callback('connexion', addr)
            # Lire les 4 premiers octets pour la taille du header
            header_size_bytes = recv_all(conn, 4)
            header_size = struct.unpack('>I', header_size_bytes)[0]
            # Lire le header JSON
            header_json = recv_all(conn, header_size)
            header = unpack_header(header_size_bytes + header_json)
            
            filename = header['filename']
            filesize = header['filesize']
            expected_hash = header['checksum']
            is_dir = header.get('is_dir', False)
            
            if self.callback:
                self.callback('recu_info', {'filename': filename, 'taille': filesize, 'is_dir': is_dir})
            
            filepath = RECEIVE_DIR / filename
            recu = 0
            with open(filepath, 'wb') as f:
                while recu < filesize:
                    chunk = conn.recv(min(CHUNK_SIZE, filesize - recu))
                    if not chunk:
                        raise ConnectionError("Connexion interrompue")
                    f.write(chunk)
                    recu += len(chunk)
                    if self.callback:
                        self.callback('progress', recu)
            
            # Verification checksum
            h = hashlib.md5()
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    h.update(chunk)
            
            if h.hexdigest() != expected_hash:
                filepath.unlink()
                if self.callback:
                    self.callback('erreur', 'Checksum invalide')
                return

            if is_dir:
                if self.callback:
                    self.callback('info', f'Extraction de {filename}...')
                # Extraire le zip dans un dossier du même nom
                extract_path = RECEIVE_DIR / filename.replace('.zip', '')
                extract_path.mkdir(exist_ok=True)
                shutil.unpack_archive(str(filepath), str(extract_path))
                filepath.unlink() # Supprimer le zip après extraction
                if self.callback:
                    self.callback('fini', extract_path.name)
            else:
                if self.callback:
                    self.callback('fini', filename)
                    
        except Exception as e:
            if self.callback:
                self.callback('erreur', str(e))
            if filepath and filepath.exists():
                filepath.unlink()
        finally:
            conn.close()
