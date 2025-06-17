import hashlib

CHUNK_SIZE = 4 * 1024 * 1024  # 4MB
SPLIT_THRESHOLD = 20 * 1024 * 1024  # 20MB

def split_into_chunks(data: bytes) -> list:
    """
    Splits the data into 4MB chunks if data size > 20MB.
    Otherwise, returns the full data as a single chunk.
    """
    if len(data) <= SPLIT_THRESHOLD:
        print("Total chunks: 1")
        return [data]  # No chunking, treat as single chunk
    chunks = [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
    print(f"Total chunks: {len(chunks)}")
    return chunks

def sha256(data: bytes) -> str:
    """
    Returns the SHA-256 hash of the input data.
    """
    return hashlib.sha256(data).hexdigest()
