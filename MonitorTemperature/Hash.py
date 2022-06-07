#! /usr/bin/env python3
#
# Pearson's hash for an 8 bit non-cryptographic result
#
# June-2022, Pat Welch, pat@mousebrains.com

__hashSalt = 0x67 # Initial salt for the hashing
__hashTable = [ # Generated from random.shuffle of list(range(256))
    79, 69, 243, 139, 251, 181, 236, 25, 58, 9, 56, 71, 178, 40, 105, 19, 31, 120, 194, 219,
    137, 101, 156, 141, 67, 157, 200, 159, 8, 118, 215, 51, 192, 36, 44, 65, 166, 180, 210,
    95, 197, 2, 108, 187, 114, 145, 111, 60, 143, 207, 82, 59, 142, 11, 188, 235, 185, 48,
    231, 10, 13, 144, 126, 47, 94, 75, 0, 1, 202, 198, 34, 109, 227, 15, 176, 81, 78, 203,
    61, 165, 18, 154, 68, 17, 135, 152, 26, 222, 218, 27, 64, 162, 170, 149, 211, 239, 131,
    38, 33, 244, 247, 121, 182, 255, 43, 184, 3, 74, 46, 37, 212, 55, 14, 248, 186, 98, 76,
    22, 97, 229, 53, 164, 45, 130, 77, 12, 39, 70, 28, 92, 252, 49, 147, 107, 155, 177, 242,
    151, 230, 85, 63, 209, 66, 190, 150, 246, 100, 253, 127, 174, 204, 217, 179, 4, 183, 163,
    73, 32, 129, 112, 96, 117, 140, 160, 41, 205, 189, 224, 80, 223, 201, 124, 226, 254, 104,
    62, 206, 213, 249, 220, 173, 245, 238, 116, 214, 146, 93, 234, 193, 158, 136, 7, 20, 195,
    24, 91, 88, 113, 50, 119, 99, 115, 110, 103, 35, 233, 132, 122, 161, 167, 5, 16, 169, 57,
    232, 138, 30, 171, 216, 86, 84, 134, 196, 128, 21, 208, 23, 87, 153, 72, 125, 29, 199, 83,
    241, 148, 42, 228, 250, 237, 172, 89, 106, 52, 6, 240, 221, 225, 175, 168, 191, 54, 90,
    133, 102, 123]

def hash8Integer(data:bytes) -> int:
    hash = (__hashSalt + len(data)) % 256 # Initial salt
    for c in data:
        hash = __hashTable[hash ^ c]
    return hash

def hash8(data:bytes) -> bytes:
    return hash8Integer(data).to_bytes(1, byteorder="big", signed=False)

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("str", type=str, nargs="+", help="Strings to hash")
    args = parser.parse_args()

    for item in args.str:
        print(item, "->", hash8(bytes(item, "utf-8")))
