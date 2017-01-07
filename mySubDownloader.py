#!/usr/bin/env python

import sys
import os
import hashlib
import urllib
import requests
import argparse
import io

try:
    from pync import Notifier
except ImportError:
    class Notifier(object):
        @staticmethod
        def notify(string, title):
            pass


def get_hash(name):
    """
    Calcualtes the hash of the file
    """
    readsize = 64 * 1024
    with open(name, 'rb') as f:
        size = os.path.getsize(name)
        data = f.read(readsize)
        f.seek(-readsize, os.SEEK_END)
        data += f.read(readsize)
    return hashlib.md5(data).hexdigest()


def main(argv=None):
    """
    This is the entry point of the program
    """
    parser = argparse.ArgumentParser(
        description="""
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('files', type=str, metavar="FILE", nargs="+",
                        help="Video files")
    parser.add_argument('--languages', type=str, metavar="LANG", default=["es", "en"], nargs="+",
                        help="Search the subtitle in the following languages")
    args = parser.parse_args()

    user_agent = "SubDB/1.0 (mySubDownloader/0.1 http://)"
    base_url = "http://api.thesubdb.com/?"

    files = []
    for i in args.files:
        try:
            tmp = {}
            tmp['filename'] = os.path.basename(i)
            tmp['path'] = os.path.dirname(i)
            tmp['hash'] = get_hash(i)
            files.append(tmp)
        except IOError:
            print "Error generating the hash for file '%s'. Maybe is it less than 64KB?" % i

    headers = {
        'User-Agent': user_agent
    }

    downloaded_ok = 0
    downloaded_nok = 0
    try:
        for i in files:
            subtitle_base_filename, extension = os.path.splitext(i['filename'])
            for j in args.languages:
                query = {
                    'action': 'download',
                    'hash': i['hash'],
                    'language': j}
                full_url = base_url + urllib.urlencode(query)
                req = requests.get(full_url, headers=headers, stream=True)
                filename = os.path.join(
                    i['path'],
                    "{base_file_name}.{language_code}.srt".format(
                        base_file_name=subtitle_base_filename,
                        language_code=j))
                print "(%s) %s" % (req.status_code, filename)
                if req.ok:
                    downloaded_ok += 1
                    with io.open(filename, 'w', encoding=req.encoding) as subtitle_file:
                        for block in req.iter_content(1024):
                            subtitle_file.write(block.decode(req.encoding))
                else:
                    downloaded_nok += 1
    except requests.exceptions.ConnectionError as connection_excpt:
        print connection_excpt
        Notifier.notify(connection_excpt, title="Error connecting to subtitles server")
    # TODO except file errors
    else:
        Notifier.notify(
            "Downloaded: %d\nNot found: %d" % (downloaded_ok, downloaded_nok),
            title="Subtitles downloaded (%s)" % (",".join(args.languages)))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
