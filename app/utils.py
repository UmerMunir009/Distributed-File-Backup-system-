import requests
import itertools

NODE_PORTS = [5001, 5002, 5003, 5004]
NODE_URLS = [f"http://127.0.0.1:{port}" for port in NODE_PORTS]

# Round-robin iterator
node_cycle = itertools.cycle(NODE_URLS)

def upload_to_node(blob: bytes, chunk_hash: str) -> str:
    """Uploads chunk to one node (round-robin). Returns node URL if success."""
    for _ in range(len(NODE_URLS)):
        node_url = next(node_cycle)
        try:
            response = requests.post(f"{node_url}/store", files={"file": ("chunk", blob)})
            if response.status_code == 200:
                print(f"[✓] Uploaded {chunk_hash} to {node_url}")
                return node_url
            else:
                print(f"[×] Failed to upload to {node_url}: {response.status_code}")
        except Exception as e:
            print(f"[!] Exception uploading to {node_url}: {e}")
    raise Exception("All nodes failed to store chunk")

def upload_to_all_nodes(blob: bytes, chunk_hash: str) -> list:
    """Uploads same chunk to all nodes. Returns list of successful node URLs."""
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
        raise Exception("Failed to replicate chunk to any node")
    return successful_nodes
