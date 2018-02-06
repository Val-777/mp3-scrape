from bs4 import BeautifulSoup
import requests
import taglib
import os

downpage = 'http://tut-audio.su/mp3-album-the-international-conspiracy-download-6081994.html'
page = requests.get(downpage)
soup = BeautifulSoup(page.content, 'html.parser')

url = 'http://tut-audio.su'

album = soup.find(id="titlealb").get_text()[:-14]
year = soup.find(id="dopinfoalb").find('p').find('b').get_text()
image_url = url + soup.find(id="imagesalb").get('src')

directory = '[{}] {}'.format(year, album)
if not os.path.exists(directory):
    os.makedirs(directory)

r = requests.get(image_url)
with open('{}/cover.jpg'.format(directory), 'wb') as f:
    f.write(r.content)


t = soup.find_all("div", "player")[0]
# _, _, offset, _ = t['data-mp3url'].split('/')
# offset = int(offset)
links = soup.find_all("div", "player")
total_tracks = len(links)
track_counter = 1
for link in links:
    track = {}
    track['interpret'], track['trackname'] = link['data-title'].split(' — ')
    _, _, _, filename = link['data-mp3url'].split('/')
    number = str(track_counter)
    if len(number) == 1:
        track['number'] = '0' + number
    else:
        track['number'] = number
    track['album'] = album
    track['filename'] = '{} {}.mp3'.format(track['number'], track['trackname'])
    track['year'] = year
    track['dllink'] = url + link['data-mp3url']

    r = requests.get(track['dllink'])
    with open('{}/{}'.format(directory, track['filename']), 'wb') as f:
        f.write(r.content)
    print(r.status_code)

    print(track['filename'])
    if r.status_code is 200:
        song = taglib.File('{}/{}'.format(directory, track['filename']))
        song.tags['TITLE'] = [track['trackname']]
        song.tags['ALBUM'] = [track['album']]
        song.tags['TRACKNUMBER'] = [
            '{}/{}'.format(track['number'], total_tracks)]
        song.tags['DATE'] = [track['year']]
        song.tags['ARTIST'] = [track['interpret']]
        song.save()
    print('-------------------------')
    track_counter += 1
