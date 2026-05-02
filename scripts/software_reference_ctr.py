#!/usr/bin/env python3
"""
Software AES-128 CTR reference for image-byte data.
"""

from pathlib import Path
import argparse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def aes_ecb_block_encrypt(key: bytes, block: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    enc = cipher.encryptor()
    return enc.update(block) + enc.finalize()

def xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))

def int_to_16b(i: int) -> bytes:
    return i.to_bytes(16, byteorder="big")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_raw", type=Path)
    ap.add_argument("--key", default="000102030405060708090A0B0C0D0E0F")
    ap.add_argument("--counter0", default="F0E0D0C0B0A090807060504030201000")
    ap.add_argument("--output", type=Path, default=Path("encrypted_ctr.raw"))
    args = ap.parse_args()

    key = bytes.fromhex(args.key)
    counter = int(args.counter0, 16)
    plain = args.input_raw.read_bytes()

    if len(plain) % 16 != 0:
        # pad to multiple of 16 for this demo scaffold
        pad_len = 16 - (len(plain) % 16)
        plain += bytes([0] * pad_len)

    out = bytearray()

    for blk_idx in range(0, len(plain), 16):
        pblk = plain[blk_idx:blk_idx+16]
        ctr_block = int_to_16b(counter)
        ks = aes_ecb_block_encrypt(key, ctr_block)
        cblk = xor_bytes(pblk, ks)
        out.extend(cblk)
        counter += 1

    args.output.write_bytes(bytes(out))
    print(f"Saved: {args.output}")

if __name__ == "__main__":
    main()
