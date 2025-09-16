import heapq
from collections import Counter, namedtuple

# Node structure
class Node(namedtuple("Node", ["char", "freq", "left", "right"])):
    def __lt__(self, other):  # needed for heapq
        return self.freq < other.freq

# Build Huffman Tree
def build_huffman_tree(text):
    freq = Counter(text)  #  frequency count
    heap = [Node(ch, fr, None, None) for ch, fr in freq.items()]
    heapq.heapify(heap)  #  min-heap
    
    while len(heap) > 1:  # combine until one node remains
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(None, left.freq + right.freq, left, right)
        heapq.heappush(heap, merged)
    
    return heap[0]  # root node

# Generate Huffman Codes
def generate_codes(node, prefix="", codebook={}):
    if node is None:
        return
    
    if node.char is not None:  # leaf node
        codebook[node.char] = prefix
    else:
        generate_codes(node.left, prefix + "0", codebook)
        generate_codes(node.right, prefix + "1", codebook)
    
    return codebook

# Encode text
def huffman_encode(text):
    root = build_huffman_tree(text)
    codes = generate_codes(root)
    encoded = "".join(codes[ch] for ch in text)
    return encoded, codes

# Decode text
def huffman_decode(encoded, codes):
    reverse_codes = {v: k for k, v in codes.items()}
    decoded, code = "", ""
    for bit in encoded:
        code += bit
        if code in reverse_codes:
            decoded += reverse_codes[code]
            code = ""
    return decoded


# Example
text = "huffman coding greedy approach"
encoded, codes = huffman_encode(text)
decoded = huffman_decode(encoded, codes)

print("Original Text:", text)
print("Huffman Codes:", codes)
print("Encoded Text:", encoded)
print("Decoded Text:", decoded)
