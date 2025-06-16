from flask import Flask, request, send_file, jsonify
import os
import hashlib
import argparse

app = Flask(__name__)
storage_path = ""  # Will be set via CLI args

@app.route('/store', methods=['POST'])
def store():
    file = request.files['file']
    content = file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    filepath = os.path.join(storage_path, file_hash)
    try:
        with open(filepath, 'wb') as f:
            f.write(content)
        print(f"[STORE] Stored chunk {file_hash} at {filepath}")
        return jsonify({'status': 'stored', 'hash': file_hash})
    except Exception as e:
        print(f"[ERROR][STORE] Failed to save {file_hash}: {e}")
        return jsonify({'error': 'Storage failed'}), 500

@app.route('/retrieve', methods=['GET'])
def retrieve():
    file_hash = request.args.get('hash')
    filepath = os.path.join(storage_path, file_hash)
    print(f"[RETRIEVE] Looking for {file_hash} at {filepath}")

    if not os.path.exists(filepath):
        print(f"[RETRIEVE] NOT FOUND: {filepath}")
        return jsonify({'error': 'Not found'}), 404

    print(f"[RETRIEVE] Found: {filepath}")
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, required=True, help="Port number to run the node on.")
    parser.add_argument('--storage', type=str, required=True, help="Path to the storage directory.")
    args = parser.parse_args()

    # Make path relative to script location, not terminal
    base_dir = os.path.dirname(os.path.abspath(__file__))
    storage_path = os.path.abspath(os.path.join(base_dir, args.storage))
    os.makedirs(storage_path, exist_ok=True)

    print(f"[INIT] Node starting on port {args.port}")
    print(f"[INIT] Using storage path: {storage_path}")

    app.run(port=args.port)
