import requests
import itertools

NODE_PORTS = [5001, 5002, 5003, 5004]
NODE_URLS = [f"http://127.0.0.1:{port}" for port in NODE_PORTS]

# Round-robin iterator
node_cycle = itertools.cycle(NODE_URLS)


def upload_to_node(blob: bytes, chunk_hash: str) -> str:
    """
    Uploads a chunk to two nodes using round-robin.
    Returns the two node URLs joined by a comma.
    """
    assigned_nodes = []

    for _ in range(2):  # select 2 different nodes
        tried = 0
        while tried < len(NODE_URLS):
            node_url = next(node_cycle)
            if node_url not in assigned_nodes:
                try:
                    response = requests.post(f"{node_url}/store", files={"file": ("chunk", blob)})
                    if response.status_code == 200:
                        print(f"[✓] Uploaded {chunk_hash} to {node_url}")
                        assigned_nodes.append(node_url)
                        break
                    else:
                        print(f"[×] Failed to upload to {node_url}: {response.status_code}")
                except Exception as e:
                    print(f"[!] Exception uploading to {node_url}: {e}")
            tried += 1

    if len(assigned_nodes) < 2:
        raise Exception(f"[ERROR] Failed to store chunk {chunk_hash} on 2 nodes")

    return ','.join(assigned_nodes)


def upload_to_all_nodes(blob: bytes, chunk_hash: str) -> list:
    """
    Uploads the same chunk to all nodes (replication).
    Returns a list of successful node URLs.
    """
    successful_nodes = []
    for node_url in NODE_URLS:
        try:
            response = requests.post(f"{node_url}/store", files={"file": ("chunk", blob)})
            if response.status_code == 200:
                print(f"[✓] Replicated {chunk_hash} to {node_url}")
                successful_nodes.append(node_url)
            else:
                print(f"[×] Failed to replicate to {node_url}: {response.status_code}")
        except Exception as e:
            print(f"[!] Exception replicating to {node_url}: {e}")

    if not successful_nodes:
        raise Exception(f"[ERROR] Failed to replicate chunk {chunk_hash} to any node")

    return successful_nodes
