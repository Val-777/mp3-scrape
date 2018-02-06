from requests.exceptions import ConnectionError
from time import time, localtime, strftime
from datetime import timedelta, datetime
from pytz import timezone

from bs4 import BeautifulSoup
import requests
import codecs

import textwrap as tw

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime  # , func
from sqlalchemy.orm import relationship, sessionmaker

from utils import (convert_size,
                   requests_retry_session,
                   unescape,
                   create_connection)


BASE = 12
LOGFILE = 'logfile_test.txt'
SEPARATOR = '-------------------------------------------------------------------------------------------\n'


def datetime_berlin():
    return datetime.now(timezone('Europe/Berlin'))


def write_to_log(messages):
    for message in messages:
        print(message[:-1])
    file = codecs.open(LOGFILE, 'a', 'utf-8')
    for message in messages:
        file.writelines(message)
    file.close()


url = 'http://tut-audio.su'

page = requests.get(url)
soup = BeautifulSoup(page.content, 'html.parser')

letter_links = []
for i in range(2):
    for link in soup.find_all("div", "letters")[i].find_all('a'):
        letter_links.append(link.get('href'))

url_letter = url + letter_links[0]

page = requests.get(url_letter)
soup = BeautifulSoup(page.content, 'html.parser')

categories = []
while True:
    for category in soup.find_all("li", "artist_num"):
        art = {'name': category.find('h2').find(
            'b').get_text(), 'url': category.find('a').get('href')}
        categories.append(art)

    if soup.find("a", text="Next"):
        next_link = soup.find("a", text="Next").get('href')
        page = requests.get(url + next_link)
        soup = BeautifulSoup(page.content, 'html.parser')
        print(next_link)
    else:
        break


database = 'mp3database{}.db'.format(BASE)

create_connection(
    "C:/Users/val31/Desktop/Projects/mp3scrape/{}".format(database))

Base = declarative_base()


class Artist(Base):
    __tablename__ = 'artist'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    created_date = Column(DateTime, default=datetime_berlin)
    updated_date = Column(DateTime, default=datetime_berlin)
    albums = relationship('Album', back_populates="artist")
#     tracks = relationship('Track', back_populates="artist")

    def __repr__(self):
        return "<Artist({})>".format(self.name)


class Album(Base):
    __tablename__ = 'album'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    year = Column(Integer)
    url = Column(String)
    cover_url = Column(String)
    number_of_tracks = Column(Integer)
    live_tracks = Column(Integer)
    genre = Column(String)
    created_date = Column(DateTime, default=datetime_berlin)
    updated_date = Column(DateTime, default=datetime_berlin)

    artist_id = Column(Integer, ForeignKey('artist.id'))
    artist = relationship("Artist", back_populates="albums",
                          foreign_keys=[artist_id])

    tracks = relationship('Track', back_populates="album")

    def verbose(self):
        print('Name: {}'.format(self.name))
        print('Artist: {}'.format(self.artist.name))
        print('Genre: {}'.format(self.genre))
        print('Year: {}'.format(self.year))
        print('Number of tracks: {}'.format(self.number_of_tracks))
        print('Number of live tracks: {}'.format(self.live_tracks))
        print('URL: {}'.format(self.url))
        print('Cover URL: {}'.format(self.cover_url))
        print('ID: {}'.format(self.id))
        print('Created: {}'.format(self.created_date))
        print('Last Update: {}'.format(self.updated_date))

    def __repr__(self):
        if self.year:
            return "<Album({} by {} from {})>".format(self.name, self.artist.name, self.year)
        else:
            return "<Album({} by {})>".format(self.name, self.artist.name)


class Track(Base):
    __tablename__ = 'track'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Integer)
    url = Column(String)
    number = Column(Integer)
    live = Column(Boolean)
    size = Column(Integer)
    created_date = Column(DateTime, default=datetime_berlin)
    updated_date = Column(DateTime, default=datetime_berlin)

#     artist_id = Column(Integer, ForeignKey('artist.id'))
#     artist = relationship("Artist", back_populates="tracks", foreign_keys=[artist_id])

    album_id = Column(Integer, ForeignKey('album.id'))
    album = relationship("Album", back_populates="tracks")

    def verbose(self):
        print('Name: {}'.format(self.name))
        # print('Artist: {}'.format(self.artist.name))
        print('Year: {}'.format(self.year))
        print('Number: {} / {}'.format(self.number, self.album.number_of_tracks))
        print('URL: {}'.format(self.url))
        print('ID: {}'.format(self.id))
        print('Size: {}'.format(convert_size(self.size)))
        print('Created: {}'.format(self.created_date))
        print('Last Update: {}'.format(self.updated_date))
        if self.live:
            status = 'Live'
        else:
            status = 'Missing'
        print('Status: {}'.format(status))

    def __repr__(self):
        return "<Track({} by {})>".format(self.name, self.album.artist.name)


engine = create_engine('sqlite:///{}'.format(database, echo=False))
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def collect_album_info(album_soup):
    url = 'http://tut-audio.su'
    album_dict = {}
    album_dict['name'] = unescape(
        album_soup.find(id="titlealb").get_text()[:-14])
    album_dict['year'] = album_soup.find(
        id="dopinfoalb").find('p').find('b').get_text()
    if album_dict['year']:
        album_dict['year'] = int(album_dict['year'])
    album_dict['cover_url'] = url + album_soup.find(id="imagesalb").get('src')
    t = album_soup.find_all("div", "player")[0]
    artist, _ = t['data-title'].split(' — ')
    artist = unescape(artist)
    album_dict['url'] = url + album_url
    return album_dict, artist


def create_album(album_dict):
    db_album = Album(**album_dict)
    session.add(db_album)
    session.commit()
    write_to_log([tw.indent('This album has been added to the data base:\n', '   '),
                  tw.indent('Artist: {}\n'.format(
                      db_album.artist.name), '     '),
                  tw.indent('Album name: {}\n'.format(db_album.name), '     '),
                  tw.indent('Year: {}\n'.format(db_album.year), '     '),
                  tw.indent('Cover: {}\n'.format(db_album.cover_url), '     ')])
    return db_album


def get_tracks(album, links):
    track_num = 1
    for link in links:
        track = {}
        _, track['name'] = link['data-title'].split(' — ')
        track['year'] = album.year
        track['album'] = album
        track['name'] = unescape(track['name'])
        track['number'] = track_num
        track['url'] = url + link['data-mp3url']
        new_track = Track(**track)
        session.add(new_track)
        track_num += 1
    session.commit()
    return track_num


def retrieve_or_create(artist_name):
    db_artist = session.query(Artist).filter_by(name=artist_name).first()
    if not db_artist:
        db_artist = Artist(name=artist_name)
        session.add(db_artist)
        session.commit()
        write_to_log(
            [tw.indent('New Artist {} added to data base!\n'.format(db_artist.name), '   ')])
        added = True
    else:
        write_to_log(
            [tw.indent('Artist {} retrieved from data base!\n'.format(db_artist.name), '   ')])
        added = False
    return db_artist, added


file = open(LOGFILE, 'w')
file.close()
start = time()
write_to_log([('Started at: {}\n'.format(
    strftime("%a, %d %b %Y %H:%M:%S +0000", localtime(start))))])
cats = categories
# cats = [{'name': '0800', 'url': '/music-file/0800'}, ]
# cats = [{'name': '007-man', 'url': '/music-file/007-man'}, ]
# cats = [{'name': '08001', 'url': '/music-file/08001'}, ]
cats = [{'name': '007-band', 'url': '/music-file/007-band'}, ]
alben = []
artists_added = 0
albums_added = 0
tracks_added = 0
# missing_tracks = 0
connection_errors = 0
# timeouts = []
for category in cats:
    page = requests.get(url + category['url'])
    if page.status_code == 404:
        write_to_log([SEPARATOR, 'Category {} has no music\n'.format(
            category['name']), SEPARATOR])
    elif page.status_code == 200:
        write_to_log(['Category {} has music!\n'.format(category['name'])])
        album_num = 0
        for i in range(1, 10):
            write_to_log([tw.indent('Try No. {}\n'.format(i), ' ')])
            soup = BeautifulSoup(page.content, 'html.parser')
            while True:
                tracks = soup.find_all('div', 'player')
                for track in tracks:
                    try:
                        album_url = track.find(
                            'div', 'track-info').find('div').find('a').get('href')
                        if album_url not in alben:
                            try:
                                al_page = requests.get(url + album_url)
                            except (ConnectionError or ConnectionResetError) as e:
                                write_to_log([e])
                                connection_errors += 1
                                al_page = requests.get(url + album_url)
                            if al_page.status_code == 200:
                                alben.append(album_url)
                                album_num += 1
                                write_to_log(
                                    [tw.indent('Found: {} ({}) \n'.format(url + album_url, album_num), '  ')])
                                album_soup = BeautifulSoup(
                                    al_page.content, 'html.parser')
                                links_to_tracks = album_soup.find_all(
                                    "div", "player")

                                album_dict, artist_name = collect_album_info(
                                    album_soup)
                                album_dict['artist'], added = retrieve_or_create(
                                    artist_name)
                                if added:
                                    artists_added += 1

                                db_album = session.query(Album).filter_by(
                                    name=album_dict['name']).first()

                                if db_album and (db_album.url == (url + album_url)):
                                    write_to_log([tw.indent('The album {} by {} is already in the data base!\n'.format(
                                        album_dict['name'], db_album.artist.name), '   ')])
                                    write_to_log([tw.indent(SEPARATOR, '   ')])
                                    album_num -= 1
                                else:
                                    album = create_album(album_dict)
                                    # missing, live, timeouts_alb = get_tracks(
                                    #     album, links_to_tracks)
                                    track_num = get_tracks(
                                        album, links_to_tracks)
                                    # print('Missing: {}, Live: {}, Timeouts: {}\n'.format(
                                    #     missing, live, timeouts_alb))
                                    # album.live_tracks = live
                                    # album.number_of_tracks = live + missing
                                    album.number_of_tracks = track_num
                                    session.commit()
                                    # missing_tracks += missing
                                    # tracks_added += live
                                    tracks_added += track_num
                                    write_to_log([SEPARATOR])
                                    # timeouts += timeouts_alb
                    except AttributeError as e:
                        print(e)
                        print(track)

                if soup.find("a", text="Next"):
                    next_link = soup.find("a", text="Next").get('href')
                    al_page = requests.get(url + next_link)
                    soup = BeautifulSoup(al_page.content, 'html.parser')
                    write_to_log(['  {}\n'.format(next_link)])
                else:
                    break
        write_to_log([SEPARATOR, 'Added {} Albums to the database of {}\n'.format(
            album_num, category['name']), SEPARATOR])
        albums_added += album_num
    else:
        write_to_log(['Category: {}, status code: {}\n'.format(
            category['name'], page.status_code)])

end = time()
endtime = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime(end))
elapsed = timedelta(seconds=end - start)
write_to_log(['Ended at {}, so needed {}\n'.format(endtime, elapsed)])
write_to_log(['Artists added to data base: {}\n'.format(artists_added)])
write_to_log(['Albums added to data base: {}\n'.format(albums_added)])
write_to_log(['Tracks added to data base: {}\n'.format(tracks_added)])
# write_to_log(['Missing tracks: {}\n'.format(missing_tracks)])
write_to_log(['Connection errors: {}\n'.format(connection_errors)])
# write_to_log(['Timeouts: {}\n'.format(len(timeouts))])
# write_to_log(['{}\n'.format(timeout_link) for timeout_link in timeouts])
