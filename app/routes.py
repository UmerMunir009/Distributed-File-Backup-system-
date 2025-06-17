from flask import Blueprint, render_template, request, redirect, url_for, send_file
import os
from io import BytesIO
import requests

from .encryption import encrypt_data, decrypt_data
from .chunking import split_into_chunks, sha256
from .utils import upload_to_node, upload_to_all_nodes, NODE_URLS

main = Blueprint('main', __name__)

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
FILE_METADATA_PATH = os.path.join(UPLOAD_FOLDER, 'metadata.txt')

SPLIT_THRESHOLD = 20 * 1024 * 1024  # 20MB


@main.route('/')
def index():
    files = []
    if os.path.exists(FILE_METADATA_PATH):
        with open(FILE_METADATA_PATH, 'r') as f:
            files = [line.strip().split('|')[0] for line in f if '|' in line]
    return render_template('index.html', files=files)


@main.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('file')
    password = request.form['password']

    for file in files:
        filename = file.filename
        raw_data = file.read()
        print(f"[UPLOAD] Received file: {filename} ({len(raw_data)} bytes)")

        encrypted_data = encrypt_data(raw_data, password)
        print(f"[UPLOAD] Encrypted size: {len(encrypted_data)} bytes")

        chunk_info = []

        if len(encrypted_data) <= SPLIT_THRESHOLD:
            # Replicate full encrypted file to all nodes
            chunk_hash = sha256(encrypted_data)
            urls = upload_to_all_nodes(encrypted_data, chunk_hash)
            for url in urls:
                chunk_info.append((chunk_hash, url))
            print(f"[UPLOAD] Replicated to all nodes")
        else:
            # Split into chunks and upload each to two nodes
            chunks = split_into_chunks(encrypted_data)
            print(f"[UPLOAD] Splitting into {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                chunk_hash = sha256(chunk)
                node_urls = upload_to_node(chunk, chunk_hash)  # "url1,url2"
                for node_url in node_urls.split(','):
                    print(f"[UPLOAD] Chunk {i}: {chunk_hash} → {node_url}")
                    chunk_info.append((chunk_hash, node_url))

        _save_metadata(filename, chunk_info)
        print(f"[UPLOAD] Metadata saved for {filename}")

    return redirect(url_for('main.index'))


def _save_metadata(filename, chunk_info):
    with open(FILE_METADATA_PATH, 'a') as f:
        chunk_str = ','.join(f"{h}@{url}" for h, url in chunk_info)
        f.write(f"{filename}|{chunk_str}\n")


@main.route('/download/<filename>', methods=['POST'])
def download_file(filename):
    password = request.form['password']
    print(f"[DOWNLOAD] Requested: {filename}")

    if not os.path.exists(FILE_METADATA_PATH):
        return "No metadata found", 404

    with open(FILE_METADATA_PATH, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith(filename + '|'):
            _, chunk_part = line.strip().split('|', 1)
            chunk_nodes = [p.split('@') for p in chunk_part.split(',')]

            full_data = b''

            # Check if all hashes are same = full file replicated
            is_replicated = all(chunk_hash == chunk_nodes[0][0] for chunk_hash, _ in chunk_nodes)

            if is_replicated:
                chunk_hash = chunk_nodes[0][0]
                for _, node_url in chunk_nodes:
                    try:
                        print(f"[DOWNLOAD] Trying {node_url} for chunk {chunk_hash}")
                        resp = requests.get(f"{node_url}/retrieve", params={'hash': chunk_hash})
                        if resp.status_code == 200:
                            full_data = resp.content
                            print(f"[DOWNLOAD] Fetched chunk from {node_url}")
                            break
                        else:
                            print(f"[ERROR] Failed from {node_url}")
                    except Exception as e:
                        print(f"[ERROR] Exception from {node_url}: {e}")
                else:
                    return f"Chunk {chunk_hash} unavailable from all nodes", 500
            else:
                # Reconstruct full file from chunked data
                chunk_map = {}
                for chunk_hash, node_url in chunk_nodes:
                    if chunk_hash not in chunk_map:
                        chunk_map[chunk_hash] = []
                    chunk_map[chunk_hash].append(node_url)

                for chunk_hash, urls in chunk_map.items():
                    for node_url in urls:
                        try:
                            print(f"[DOWNLOAD] Trying {node_url} for chunk {chunk_hash}")
                            resp = requests.get(f"{node_url}/retrieve", params={'hash': chunk_hash})
                            if resp.status_code == 200:
                                full_data += resp.content
                                print(f"[DOWNLOAD] Fetched chunk from {node_url}")
                                break
                        except Exception as e:
                            print(f"[ERROR] Exception from {node_url}: {e}")
                    else:
                        return f"Chunk {chunk_hash} unavailable from all nodes", 500

            try:
                decrypted_data = decrypt_data(full_data, password)
                print(f"[DOWNLOAD] Decryption successful")
                return send_file(BytesIO(decrypted_data), as_attachment=True, download_name=filename)
            except Exception as e:
                print(f"[ERROR] Decryption failed: {e}")
                return f"Decryption failed: {str(e)}", 400

    print(f"[ERROR] File not found in metadata: {filename}")
    return "File not found", 404
