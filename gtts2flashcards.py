from __future__ import print_function
import os
import shutil
import httplib2

from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from gtts import gTTS
from datetime import datetime as dt

SHEET_SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
DRIVE_SCOPES = 'https://www.googleapis.com/auth/drive.file'
SHEET_JSON_NAME = 'sheet2flashcards.json'
DRIVE_JSON_NAME = 'upload2gdrive.json'
SHEET_ID = <SpreadsheetのID>
DRIVE_ID = <Goggle DriveのID
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google API Python Client'
MAX_COLUMN = 4
TEXT1 = 0
TEXT2 = 1
SOUND2 = 3

try:
    import argparse
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.add_argument('--update',
                        action='store_true',
                        default=False,
                        help='update all contents (default: False)')
    flags = parser.parse_args()
except ImportError:
    flags = None

# 認証
def get_credentials(scopes, json_name):
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, json_name)

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, scopes)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

# Google SpreadsheetにMP3のファイル名を追加
def append_mp3name_to_gsheet():
    credentials = get_credentials(SHEET_SCOPES, SHEET_JSON_NAME)
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
                    
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range='A2:D').execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        for row in values:
            if len(row) < MAX_COLUMN:
                row.append(row[TEXT1] + '.mp3')

        value_range_body = {"range":"A2:D",
                            "majorDimension":"ROWS",
                            "values":values}
        response = service.spreadsheets().values().update(
                        spreadsheetId=SHEET_ID, range="A2:D",
                        valueInputOption='USER_ENTERED',
                        body=value_range_body).execute()
    return values

# MP3ファイルをGoogle Driveに追加（--updateオプションの場合は総入れ替え)
def mp3_to_gdrive(lists):
    credentials = get_credentials(DRIVE_SCOPES, DRIVE_JSON_NAME)
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    
    datetime = dt.now()
    dirname = datetime.strftime('%Y%m%d%H%M%S')
    os.mkdir(dirname)

    query_parents = "'" + DRIVE_ID + "'" + " in parents"

    for row in lists:
        query_mp3name = "name = " + "'" + row[SOUND2] + "'"
        results = service.files().list(
            q = query_parents + " and trashed = False and " +
                query_mp3name, 
            fields = "files(id, name)").execute()
        results = results.get('files', [])

        if not results:
            tts = gTTS(text = row[TEXT2],lang = 'en',slow = False)
            tts.save(os.path.join(dirname, row[SOUND2]))

            file_metadata = {'name':row[SOUND2], 'parents':[DRIVE_ID]}
            media_body = MediaFileUpload(os.path.join(dirname, row[SOUND2]),
                                        mimetype='audio/mp3')
            
            results = service.files().create(body=file_metadata, 
                                    media_body=media_body).execute()
        else:
            if flags.update == True:
                tts = gTTS(text = row[TEXT2], lang = 'en', slow = False)
                tts.save(os.path.join(dirname, row[SOUND2]))

                file_metadata = {'name':row[SOUND2], 'addParents':[DRIVE_ID]}
                media_body = MediaFileUpload(os.path.join(dirname, row[SOUND2]),
                                            mimetype='audio/mp3')
            
                for item in results:
                    file_id = item['id']
                    results = service.files().update(fileId=file_id,
                                        body=file_metadata, 
                                        media_body=media_body).execute()

    shutil.rmtree(dirname)
                                    
def main():
    lists = append_mp3name_to_gsheet()
    mp3_to_gdrive(lists)

if __name__ == '__main__':
    main()
