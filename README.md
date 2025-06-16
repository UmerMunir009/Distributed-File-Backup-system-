1. File Upload with Encryption
    Users can upload files via a web interface.
    A password is provided by the user.
    File data is encrypted using AES encryption before storage.

2. Smart Storage Based on File Size
✅ Files ≤ 20MB:
    Treated as single encrypted blob.
    Replicated to all storage nodes (ensures high availability).
    Stored using SHA-256 hash as filename.
✅ Files > 20MB:
    Split into 4MB encrypted chunks.
    Chunks are distributed in round-robin fashion to multiple nodes.
    Each chunk is stored by its hash.

3. Distributed Storage Nodes
    Independent Flask servers (storage_node.py), each representing a node.
    Each node:
        Accepts /store POST requests to save files.
        Responds to /retrieve GET requests to serve files by hash.

4. Metadata Management
    Stored in uploads/metadata.txt.
    Tracks:
        Original filename
        Hashes of chunks
        Node URLs storing each chunk
    Used to reconstruct and download files.

5. File Download with Decryption
    User enters the filename and password.
    System reads metadata, then:
        Tries downloading each chunk from any listed node (fault-tolerant).
    Chunks are reassembled (if applicable).
    Encrypted data is decrypted using the password.
    Final decrypted file is sent to the user.

6. Web Interface
    Upload form for selecting files and entering password.
    Displays list of uploaded filenames.
    Enables download of stored files by clicking and entering password.

7. Fault Tolerance
    For replicated files, system only needs 1 available node per chunk to retrieve data.
    Handles node unavailability by checking all possible nodes for each chunk.