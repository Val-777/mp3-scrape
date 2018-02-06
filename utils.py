import math

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

import sqlite3
from sqlite3 import Error


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "{} {}".format(s, size_name[i])


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def unescape(s):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&quot;", '"')
    s = s.replace("&apos;", "'")
    s = s.replace("&#39;", "'")
    s = s.replace("&amp;", "&")
    return s


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        conn.close()


def check_tracks(links):
    """
    Input: URL to tracks to check
    """
    pass
    # missing_tracks_from_album = 0
    # live_tracks = 0
    # total_tracks = len(links)
    # missing_tracks = []
    # timeouts = []
    # artist = session.query(Artist).filter_by(name=album.artist).first()
    # track['artist'] = unescape(track['artist'])

    # write_to_log(
    # [tw.indent('{} {}\n'.format(log_track_num, track['name']), '        ')])
    # tr_page = ''

    # t0 = time()
    # try:
    #     tr_page = requests_retry_session().head(
    #         url + link['data-mp3url'],
    #     )
    # except Exception as x:
    #     message = 'Exception: {}'.format(x.__class__.__name__)
    #     track['live'] = False
    # else:
    #     message = 'Status code: {}'.format(tr_page.status_code)
    #     if tr_page.status_code is 524:
    #         timeouts.append(url + link['data-mp3url'])
    #         write_to_log([tw.indent('Timeout!\n', '        ')])
    #     if tr_page.status_code not in [200, 524]:
    #         missing_tracks_from_album += 1
    #         write_to_log([tw.indent('Track is missing!\n', '        ')])
    #     track['live'] = False
    # finally:
    #     t1 = time()
    #     elapsed = timedelta(seconds=t1 - t0)
    #     write_to_log(
    #         [tw.indent('{} and took {}'.format(message, elapsed), '        ')])

    # if tr_page and tr_page.status_code == 200:
    # log_track_num = '{}/{}'.format(track_num, total_tracks)
    # track['live'] = True
    # live_tracks += 1
    # write_to_log(
    #     [tw.indent('{}\n'.format(url + link['data-mp3url']), '        ')])
    # return missing_tracks_from_album, live_tracks, timeouts
