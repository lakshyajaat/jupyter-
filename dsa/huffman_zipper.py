#!/usr/bin/env python3
"""
huffman_zipper.py

A simple file zipper using Huffman (greedy) coding.

Features:
- Pack multiple files into a simple archive and compress the whole archive using Huffman coding over bytes (0-255).
- Decompress and extract files to a directory.
- Pure-Python, single-file implementation.

Usage (examples):
  # Compress files into archive.hzip
  python3 huffman_zipper.py compress -o archive.hzip file1.txt image.png folder/file2.bin

  # Decompress archive.hzip into ./out_dir
  python3 huffman_zipper.py decompress -i archive.hzip -d out_dir

Notes:
- The archive format stores an internal uncompressed archive (file entries with name and sizes) which is then Huffman-compressed as a whole.
- The header contains a 256-entry frequency table (uint64 each) so the Huffman tree can be reconstructed.

Author: Lakshya
"""

import argparse
import heapq
import os
import struct
from collections import Counter
from typing import Dict, List, Tuple

MAGIC = b'HZIP'  # 4 bytes magic

class Node:
    def __init__(self, freq, byte=None, left=None, right=None):
        self.freq = freq
        self.byte = byte
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq


def build_frequency_table(data: bytes) -> List[int]:
    cnt = Counter(data)
    freqs = [0] * 256
    for b, c in cnt.items():
        freqs[b] = c
    return freqs


def build_huffman_tree(freqs: List[int]) -> Node:
    heap = []
    for byte_val, f in enumerate(freqs):
        if f > 0:
            heapq.heappush(heap, (f, Node(f, byte=byte_val)))
    # Edge case: if only one symbol present, still create a tree
    if len(heap) == 1:
        f, node = heap[0]
        return Node(f, left=node, right=None)
    while len(heap) > 1:
        f1, n1 = heapq.heappop(heap)
        f2, n2 = heapq.heappop(heap)
        merged = Node(f1 + f2, left=n1, right=n2)
        heapq.heappush(heap, (merged.freq, merged))
    if not heap:
        return None
    return heap[0][1]


def build_codes(root: Node) -> Dict[int, str]:
    codes = {}
    if root is None:
        return codes
    def dfs(node, path):
        if node.byte is not None:
            # leaf
            codes[node.byte] = path or '0'  # if single symbol, give code '0'
            return
        if node.left:
            dfs(node.left, path + '0')
        if node.right:
            dfs(node.right, path + '1')
    dfs(root, '')
    return codes


def pack_bits(bitstr: str) -> Tuple[bytes, int]:
    # Return bytes and padding bits count (not needed since we store bit length)
    total_bits = len(bitstr)
    b = bytearray()
    for i in range(0, total_bits, 8):
        chunk = bitstr[i:i+8]
        if len(chunk) < 8:
            chunk = chunk.ljust(8, '0')
        b.append(int(chunk, 2))
    return bytes(b), total_bits


def compress_data(data: bytes) -> bytes:
    freqs = build_frequency_table(data)
    root = build_huffman_tree(freqs)
    codes = build_codes(root)
    # Encode
    bits = []
    append = bits.append
    for byte in data:
        append(codes[byte])
    bitstr = ''.join(bits)
    packed_bytes, bitlen = pack_bits(bitstr)

    # Build output: MAGIC + freq table (256 Q) + orig_size (Q) + bitlen (Q) + packed_bytes
    out = bytearray()
    out += MAGIC
    # pack frequencies as 256 unsigned long long
    out += struct.pack('<256Q', *freqs)
    out += struct.pack('<Q', len(data))
    out += struct.pack('<Q', bitlen)
    out += packed_bytes
    return bytes(out)


def decompress_data(comp_bytes: bytes) -> bytes:
    # Read header
    if len(comp_bytes) < 4 or comp_bytes[:4] != MAGIC:
        raise ValueError('Not a HZIP archive or corrupt (bad magic)')
    offset = 4
    if len(comp_bytes) < offset + 256*8 + 8 + 8:
        raise ValueError('Corrupt or truncated archive')
    freqs = list(struct.unpack_from('<256Q', comp_bytes, offset))
    offset += 256*8
    orig_size = struct.unpack_from('<Q', comp_bytes, offset)[0]
    offset += 8
    bitlen = struct.unpack_from('<Q', comp_bytes, offset)[0]
    offset += 8
    packed = comp_bytes[offset:]
    # Rebuild tree
    root = build_huffman_tree(freqs)
    codes = build_codes(root)
    # Build decode map (bitstring->byte) by traversing tree
    # Instead of building a huge map, decode by walking the tree
    # Unpack bits
    bitstr = []
    for b in packed:
        bitstr.append(f'{b:08b}')
    bitstr = ''.join(bitstr)[:bitlen]

    # Decode
    if root is None:
        return b''
    out = bytearray()
    node = root
    # Special case: single-symbol tree
    single_symbol = None
    if root.byte is not None:
        single_symbol = root.byte
        return bytes([single_symbol]) * orig_size

    for bit in bitstr:
        if bit == '0':
            node = node.left
        else:
            node = node.right
        if node.byte is not None:
            out.append(node.byte)
            node = root
            if len(out) >= orig_size:
                break
    return bytes(out)


def build_uncompressed_archive(file_paths: List[str]) -> bytes:
    # Simple archive: for each file, store name length (I, 4 bytes), name (utf-8), file size (Q), file content
    parts = bytearray()
    for path in file_paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"{path} not found or not a file")
        name = os.path.basename(path).encode('utf-8')
        with open(path, 'rb') as f:
            data = f.read()
        parts += struct.pack('<I', len(name))
        parts += name
        parts += struct.pack('<Q', len(data))
        parts += data
    return bytes(parts)


def extract_uncompressed_archive(archive_bytes: bytes, out_dir: str):
    offset = 0
    os.makedirs(out_dir, exist_ok=True)
    while offset < len(archive_bytes):
        if offset + 4 > len(archive_bytes):
            raise ValueError('Corrupt internal archive (name length)')
        name_len = struct.unpack_from('<I', archive_bytes, offset)[0]
        offset += 4
        if offset + name_len > len(archive_bytes):
            raise ValueError('Corrupt internal archive (name bytes)')
        name = archive_bytes[offset:offset+name_len].decode('utf-8')
        offset += name_len
        if offset + 8 > len(archive_bytes):
            raise ValueError('Corrupt internal archive (size)')
        sz = struct.unpack_from('<Q', archive_bytes, offset)[0]
        offset += 8
        if offset + sz > len(archive_bytes):
            raise ValueError('Corrupt internal archive (file data)')
        data = archive_bytes[offset:offset+sz]
        offset += sz
        # Write file
        out_path = os.path.join(out_dir, name)
        with open(out_path, 'wb') as f:
            f.write(data)


def compress_files(file_paths: List[str], out_file: str):
    print(f'Building internal archive for {len(file_paths)} file(s) ...')
    archive = build_uncompressed_archive(file_paths)
    print(f'Internal archive size: {len(archive)} bytes')
    comp = compress_data(archive)
    with open(out_file, 'wb') as f:
        f.write(comp)
    print(f'Wrote compressed archive to {out_file} ({len(comp)} bytes)')


def decompress_file(in_file: str, out_dir: str):
    with open(in_file, 'rb') as f:
        comp = f.read()
    print(f'Read {len(comp)} bytes from {in_file}, decompressing ...')
    archive = decompress_data(comp)
    print(f'Internal archive size after decompression: {len(archive)} bytes')
    extract_uncompressed_archive(archive, out_dir)
    print(f'Extracted files to {out_dir}')


def main():
    parser = argparse.ArgumentParser(description='Huffman-based file zipper')
    sub = parser.add_subparsers(dest='cmd')

    c1 = sub.add_parser('compress', help='Compress files into a .hzip archive')
    c1.add_argument('files', nargs='+', help='Files to compress')
    c1.add_argument('-o', '--output', required=True, help='Output archive path (.hzip)')

    c2 = sub.add_parser('decompress', help='Decompress a .hzip archive')
    c2.add_argument('-i', '--input', required=True, help='Input archive path')
    c2.add_argument('-d', '--outdir', required=True, help='Output directory to extract files')

    args = parser.parse_args()
    if args.cmd == 'compress':
        compress_files(args.files, args.output)
    elif args.cmd == 'decompress':
        decompress_file(args.input, args.outdir)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
