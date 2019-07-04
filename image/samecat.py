#!/usr/bin/env python

################################################################################
# SameCat                                                                      #
################################################################################
# A program to calculate a hash of an image based on visual characteristics.   #
# Originally AverageHash                                                       #
# Author: David J. Oftedal.                                                    #
#                                                                              #
# Depends on Python Imaging Library: http://www.pythonware.com/products/pil/   #
#                                                                              #
# Thanks to:                                                                   #
# http://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html  #
# for the algorithm.                                                           #
#                                                                              #
# See http://folk.uio.no/davidjo/programming.php for original code.            #
# Modified version at http://jessekornblum.com/samecat/                        #
#                                                                              #
# Modified by Jesse Kornblum                                                   #
################################################################################
#
# Revision History
# 5 Oct 2012 - Initial release by Jesse Korbnblum


import os, sys, argparse
from PIL import Image
from PIL import ImageStat

# Files are considering matching if their AverageHash score is
# above this value
DEFAULT_MATCH_THRESHOLD = 100

SAMECAT_HEADER  = "##SAMECAT001"
SAMECAT_VERSION = "1.0"

FIRST_OUTPUT = True

def AverageHash(theImage):
    # Squeeze the image down to an 8x8 image.
    theImage = theImage.resize((8,8), Image.ANTIALIAS)
    
    # Convert it to 8-bit grayscale.
    theImage = theImage.convert("L") # 8-bit grayscale
    
    # Remove two bits to make it 6-bit grayscale.
    theImage = theImage.point(lambda pixel: pixel >> 2)
    
    # Calculate the average value.
    averageValue = ImageStat.Stat(theImage).mean[0]
    
    # Go through each pixel, from (0,0) to (0,1), (0,2), (0,3) etc.
    # Return 1-bits when the tone is equal to or above the average,
    # and 0-bits when it's below the average.
    averageHash = 0
    for row in xrange(8):
        for col in xrange(8):
            averageHash <<= 1
            averageHash |= 1 * ( theImage.getpixel((col, row)) >= averageValue)

    return averageHash


def match_score(hash1, hash2):
    '''
        Returns the Hamming distance between the two hashes
        '''
    return (((64 - bin(hash1 ^ hash2).count("1"))*100.0)/64.0)


def loadImage(fn):
    try:
        theImage = Image.open(fn)
        theImage.load()
        return theImage
    except IOError as e:
        msg = fn + ": " + str(e)
        print >> (sys.stderr, msg)
        return None


def hash_file(fn):
    '''
        Returns the hash of a specified file. If the file cannot be
        read, returns None.
        '''
    img = loadImage(fn)
    if img is None:
        return None
    
    return AverageHash(img)


def display_hash(hash,fn):
    global FIRST_OUTPUT
    
    if hash is None:
        return None
    if FIRST_OUTPUT:
        print(SAMECAT_HEADER)
        FIRST_OUTPUT = False
    print (("%s,%s" % (hash, fn)))


def display_results(args, known_files, hash, fn):
    # Calling functions may legally pass 'None' in for hash
    if hash is None:
        return True
    
    if known_files is None:
        display_hash(hash,fn)
        return False

    for k in known_files:
        score = match_score(k, hash)
        if score >= args.threshold:
            for match in known_files[k]:
                # Don't display A matches A if the user requested us not to.
                if fn == match and not args.selfmatch:
                    continue
                print (("%s matches %s (%d)" % (match, fn, score)))
    return False


def process_file(args, known_files, fn):
    '''
        Hash the unknown file (or directory fn).
        If known_files is not None, search for matches.
        If known_files is None, display the hash of fn
        '''
    
    # Note that hash_file may return None. We don't error check
    # that return value here as it's in two places. We instead
    # handle that case in display_results.
    
    if os.path.isdir(fn):
        if not args.recursive:
            msg = fn + ": Is a directory"
            print >> sys.stderr, msg
            return True
        
        for root, dirs, files in os.walk(fn):
            for f in files:
                myfn = os.path.join(root, f)
                hash = hash_file(myfn)
                display_results(args, known_files, hash, myfn)
    else:
        display_results(args, known_files, hash_file(fn), fn)
    return False


def load_known(fn):
    try:
        handle = open(fn,"rb")
    except IOError as e:
        print(e)
        return None
    
    header = handle.readline().rstrip("\r\n")
    if header != SAMECAT_HEADER:
        print ("%s: Invalid header for known files" % (fn))
        return True
    
    known_files = {}
    line_number = 1
    
    for line in handle:
        line_number += 1
        
        if line[0] == '#':
            continue
    
        line = line.rstrip("\r\n")
        words = line.split(',')
        
        if len(words) != 2:
            print ("%s: Invalid line %d. Skipping." % (fn,line_number))
            continue

    hash = long(words[0])
    if hash in known_files:
        known_files[hash].append(words[1])
    else:
        known_files[hash] = [words[1]]

    handle.close()
    return known_files


def parse_command_line():
    parser = argparse.ArgumentParser(description="Compute and match signatures for similar looking pictures")
    
    parser.add_argument("-r", "--recursive",
                        dest="recursive",
                        action="store_true",
                        help="recursively process files")
        
    parser.add_argument("-m", "--match",
                        metavar="FILE",
                        dest="match",
                        help="match against a file of known hashes")
    
    parser.add_argument("-s", "--selfmatches",
                        dest="selfmatch",
                        action="store_true",
                        help="display self matches (A matches A)")
    
    parser.add_argument("-t", "--threshold",
                        dest="threshold",
                        metavar="<value>",
                        type=int,
                        default=DEFAULT_MATCH_THRESHOLD,
                        help="set threshold for matching")
    
    parser.add_argument("files",
                        metavar='FILE',
                        nargs="*",
                        help="files to hash")
                        
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_command_line()
    
    if args.match is not None:
        known_files = load_known(args.match)
        if known_files is None:
            print ("Unable to read known hashes")
            sys.exit(1)
    else:
        known_files = None
    
    for fn in args.files:
        process_file(args, known_files,fn)

