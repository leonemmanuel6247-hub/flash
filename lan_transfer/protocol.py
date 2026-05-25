import struct
import json

HEADER_SIZE_FORMAT = '>I'
CHUNK_SIZE = 4096


def pack_header(filename, filesize, checksum, is_dir=False):
    """
    Prépare l'en-tête du transfert.
    Inclut désormais le flag 'is_dir' pour le support des dossiers.
    """
    header_dict = {
        "filename": filename,
        "filesize": filesize,
        "checksum": checksum,
        "is_dir": is_dir
    }
    header_json = json.dumps(header_dict).encode('utf-8')
    header_size = struct.pack(HEADER_SIZE_FORMAT, len(header_json))
    return header_size + header_json


def unpack_header(data):
    """
    Décode l'en-tête reçu.
    """
    header_size = struct.unpack(HEADER_SIZE_FORMAT, data[:4])[0]
    header_json = data[4:4 + header_size].decode('utf-8')
    return json.loads(header_json)


def make_chunks(filepath):
    """
    Générateur pour lire un fichier par morceaux.
    """
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            yield chunk


def recv_all(sock, size):
    """
    Garantit la réception de la totalité des octets demandés.
    """
    data = b''
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            raise ConnectionError("Connexion interrompue")
        data += packet
    return data
