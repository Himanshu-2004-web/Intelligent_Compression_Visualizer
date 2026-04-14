

from flask import Flask, render_template, request, jsonify, url_for
import heapq
from collections import Counter
import matplotlib.pyplot as plt
import graphviz
import time
import os

app = Flask(__name__)

if not os.path.exists("static"):
    os.makedirs("static")

# ---------------- HUFFMAN ----------------
class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(text):
    freq = Counter(text)
    heap = [Node(c, f) for c, f in freq.items()]
    heapq.heapify(heap)

    if len(heap) == 1:
        return heap[0], freq

    while len(heap) > 1:
        l = heapq.heappop(heap)
        r = heapq.heappop(heap)
        m = Node(None, l.freq + r.freq)
        m.left = l
        m.right = r
        heapq.heappush(heap, m)

    return heap[0], freq


def generate_codes(node, prefix="", codebook=None):
    if codebook is None:
        codebook = {}

    if node:
        if node.char is not None:
            codebook[node.char] = prefix if prefix else "0"

        generate_codes(node.left, prefix + "0", codebook)
        generate_codes(node.right, prefix + "1", codebook)

    return codebook


def encode(text, codes):
    return "".join(codes[ch] for ch in text)


def decode(encoded, codes):
    reverse = {v: k for k, v in codes.items()}
    temp = ""
    result = ""

    for bit in encoded:
        temp += bit
        if temp in reverse:
            result += reverse[temp]
            temp = ""

    return result


# ---------------- TREE ----------------
def draw_tree(root):
    from graphviz import Digraph

    dot = Digraph(format='png')
    dot.attr(rankdir='TB')  # Top to Bottom

    def add(node):
        if node is None:
            return

        label = f"{node.char}:{node.freq}" if node.char else f"{node.freq}"
        dot.node(str(id(node)), label)

        if node.left:
            left_label = f"{node.left.char}:{node.left.freq}" if node.left.char else f"{node.left.freq}"
            dot.edge(str(id(node)), str(id(node.left)), label="0")
            add(node.left)

        if node.right:
            right_label = f"{node.right.char}:{node.right.freq}" if node.right.char else f"{node.right.freq}"
            dot.edge(str(id(node)), str(id(node.right)), label="1")
            add(node.right)

    add(root)

    path = "static/tree"
    dot.render(path, cleanup=True)

    return url_for('static', filename='tree.png')


# ---------------- PROCESS ----------------
def process_text(text):
    root, freq = build_huffman_tree(text)
    codes = generate_codes(root)

    encoded = encode(text, codes)
    decoded = decode(encoded, codes)

    decoding_table = {v: k for k, v in codes.items()}

    original_bits = len(text) * 8
    compressed_bits = len(encoded)

    decoding_bits = sum(8 + len(code) for code in codes.values())
    total_bits = compressed_bits + decoding_bits

    tree_img = draw_tree(root)

    return {
        "codes": codes,
        "encoded": encoded,
        "decoded": decoded,
        "decoding": decoding_table,
        "original_bits": original_bits,
        "compressed_bits": compressed_bits,
        "decoding_bits": decoding_bits,
        "total_bits": total_bits,
        "ratio": round(total_bits / original_bits, 3),
        "tree": tree_img
    }


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/compress", methods=["POST"])
def compress():
    try:
        start = time.time()
        data = request.get_json()
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "Empty input"}), 400

        result = process_text(text)
        result["time"] = round(time.time() - start, 5)

        return jsonify(result)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload():
    try:
        start = time.time()

        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        try:
            text = file.read().decode("utf-8")
        except:
            return jsonify({"error": "Only .txt files supported"}), 400

        if not text.strip():
            return jsonify({"error": "File is empty"}), 400

        result = process_text(text)
        result["time"] = round(time.time() - start, 5)

        return jsonify(result)

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
