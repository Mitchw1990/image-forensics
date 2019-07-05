#!/usr/bin/env python

import os
import sys

from PIL import Image
from PIL import ImageStat
from PIL.WmfImagePlugin import long

FILE_HEADER = "##SAMECAT001"
FIRST_OUTPUT = True


def average_hash(image):
    image = image.resize((8, 8), Image.ANTIALIAS)  # resize
    image = image.convert("L")  # 8-bit grayscale
    image = image.point(lambda pixel: pixel >> 2)  # Remove two bits to make it 6-bit grayscale.
    average = ImageStat.Stat(image).mean[0]
    hashed_image = 0
    bit_range = range(8)

    # Go through each pixel, from (0,0) to (0,1), (0,2), (0,3) etc.
    # Return 1 if the tone is greater than or equal to the average
    # Return 0 when if it is below the average.
    for row in bit_range:
        for col in bit_range:
            hashed_image <<= 1
            hashed_image |= 1 * (image.getpixel((col, row)) >= average)

    return hashed_image


def get_hamming_distance(hash1, hash2):
    return ((64 - bin(hash1 ^ hash2).count("1")) * 100.0) / 64.0  # Hamming distance between the two hashes


def load_image(file_path):
    try:
        image = Image.open(file_path)
        image.load()
        return image

    except IOError as e:
        print(sys.stderr, file_path + ": " + str(e))
        return None


def hash_file(file_path):
    img = load_image(file_path)

    if img is None:
        return None

    return average_hash(img)


def display_hash(file_hash, file_name):
    global FIRST_OUTPUT

    if file_hash is None:
        return None

    if FIRST_OUTPUT:
        FIRST_OUTPUT = False
        print(FILE_HEADER)

    print(("%s,%s" % (file_hash, file_name)))


def display_results(args, file_hashes, file_hash, file_name):
    if file_hash is None:
        return True

    if file_hashes is None:
        display_hash(file_hash, file_name)
        return False

    for hash1 in file_hashes:
        score = get_hamming_distance(hash1, file_hash)
        if score >= args.threshold:
            for hash2 in file_hashes[hash1]:
                if file_name != hash2:
                    print(("%s matches %s (%d)" % (hash2, file_name, score)))
    return False


def process_file(arguments, file_hashes, file_dir):
    # Hash the unknown file (or directory fn).
    # If known_files is not None, search for matches.
    # If known_files is None, display the hash of fn

    # Note that hash_file may return None. We don't error check
    # that return value here as it's in two places. We instead
    # handle that case in display_results.

    if os.path.isdir(file_dir):

        if not arguments.recursive:
            print(sys.stderr, "%s: Is a directory" % file_dir)
            return True

        for dir_path, _, files_names in os.walk(file_dir):
            for file_name in files_names:
                file_path = os.path.join(dir_path, file_name)
                hashed_image = hash_file(file_path)
                display_results(arguments, file_hashes, hashed_image, file_path)

    else:
        display_results(arguments, file_hashes, hash_file(file_dir), file_dir)
    return False


def load_existing(hashes_file):
    try:
        handle = open(hashes_file, "rb")
    except IOError as e:
        print(e)
        return None

    header = handle.readline().rstrip(b'\r\n')

    if header != FILE_HEADER:
        print("%s: Invalid header for hashes file" % hashes_file)
        return True

    known_files = {}
    line_number = 1

    for line in handle:
        line_number += 1

        if line[0] == '#':
            continue

        line = line.rstrip(b'\r\n')
        words = line.split(b',')

        if len(words) != 2:
            print("%s: Invalid line %d. Skipping." % hashes_file, line_number)
            continue

        hashed_file = long(words[0])

        if hashed_file in known_files:
            known_files[hashed_file].append(words[1])
        else:
            known_files[hashed_file] = [words[1]]

    handle.close()
    return known_files


def run_compare(args):
    if args.providedHashes is not None:
        input_files = load_existing(args.providedHashes)
        if input_files is None:
            print("Unable to read known hashes.")
            sys.exit(1)
    else:
        input_files = None

    for file_dir in args.files:
        process_file(args, input_files, file_dir)
