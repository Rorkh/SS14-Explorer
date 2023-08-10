from pathlib import Path
from utils import prettydate

from datetime import datetime

import os
import sqlite3

import deflate
import zstd

content = str(Path.home() / ".local/share/Space Station 14/launcher/content.db")

if (not os.path.exists(content)):
    print('Content file is not found. Are you sure SS14 is installed properly?')
    exit()

data = Path('data')
data.mkdir(exist_ok=True)

con = sqlite3.connect(content)
cur = con.cursor()

print('Welcome to SS14 explorer')

def get_servers():
    servers = cur.execute('SELECT Id, ForkId, LastUsed FROM ContentVersion ORDER BY LastUsed DESC')
    return servers.fetchall()

def get_files(VersionId, filename):
    files = cur.execute("SELECT Path, ContentId FROM ContentManifest WHERE VersionId = {} AND Path LIKE '%{}%'".format(VersionId, filename))
    return files.fetchall()

def download_file(ContentId, filepath):
    entry = cur.execute('SELECT Compression, Data from Content WHERE Id = {}'.format(ContentId)).fetchone()
    
    Compression = entry[0]
    Data = entry[1]

    match Compression:
        case 0:
            Data = Data
        case 1:
            Data = deflate.gzip_decompress(Data)
        case 2:
            Data = zstd.decompress(Data)
    
    directory = data / os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    directory.mkdir(parents=True, exist_ok=True)
    output = directory / filename

    with open(output, 'wb') as f:
        f.write(Data)
    
    print('Saved to {}'.format(str(output)))

def search_files(VersionId):
    while True:
        print('Enter filename of file to search')
        filename = input('> ')

        files = get_files(VersionId, filename)
        
        if len(files) > 0:
            while True:
                i = 0
                for file in files:
                    print("[{}] {}".format(i, file[0]))
                    i += 1

                print('What file do you want to download (or n to cancel)')
                option = input('> ')

                if option != 'n':
                    selected_file = files[int(option)]
                    download_file(selected_file[1], selected_file[0])
                else:
                    break

def explore_files():
    servers = get_servers()

    while True:
        print('What server files do you want to explore?')

        i = 0
        for server in servers:
            ForkId = server[1] if server[1] != '' else 'unknown'
            LastUsed = datetime.strptime(server[2], '%Y-%m-%d %H:%M:%S')

            print("[{}] {} (last used {})".format(i, ForkId, prettydate(LastUsed)))
            i += 1

        server = int(input('> '))
        search_files(servers[server][0])

while True:
    print('\nChoose an option:')

    print('[1] Explore server files')
    option = input('> ')

    if str(option) == '1':
        explore_files()