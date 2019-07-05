import argparse

from image.compare import run_compare

DEFAULT_HAMMING_THRESHOLD = 100


def main():
    parser = argparse.ArgumentParser(description="Fingerprints images and returns their Hamming distance.")

    parser.add_argument("-r", "--recursive",
                        dest="recursive",
                        action="store_true",
                        help="recursively process files")

    parser.add_argument("-h", "--hashes",
                        metavar="FILE",
                        dest="providedHashes",
                        help="provide a file containing existing hashes")

    parser.add_argument("-t", "--threshold",
                        dest="threshold",
                        metavar="<value>",
                        type=int,
                        default=DEFAULT_HAMMING_THRESHOLD,
                        help="the max hamming distance for successful matches")

    parser.add_argument("files",
                        metavar='FILE',
                        nargs="*",
                        help="file(s) to hash")

    run_compare(parser.parse_args())


if __name__ == '__main__':
    main()
