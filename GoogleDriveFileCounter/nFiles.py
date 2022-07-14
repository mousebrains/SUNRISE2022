#! /usr/bin/env python3

from argparse import ArgumentParser
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import sys

def getCredentials(scopes:list[str], token:str, secret:str) -> Credentials:
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token = os.path.abspath(os.path.expanduser(token))
    if os.path.exists(token):
        creds = Credentials.from_authorized_user_file(token, args.scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret = os.path.abspath(os.path.expanduser(secret))
            flow = InstalledAppFlow.from_client_secrets_file(secret, args.scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        dirname = os.path.dirname(token)
        if not os.path.isdir(dirname):
            os.path.makedir(dirname, mode=0o700, exist_ok=True)
        with open(token, 'w') as fp: fp.write(creds.to_json())

    return creds

parser = ArgumentParser()
parser.add_argument("--scopes", type=str, action="append", help="Scopes to authenticate with")
parser.add_argument("--token", type=str, 
        default="~/.config/Google/token.json",
        help="Google API Tokens File")
parser.add_argument("--secret", type=str,
        default="~/.config/Google/sunriseCounter.secret.json",
        help="Google API Credentials File")
parser.add_argument("id", type=str, nargs="+", help="Shared folder ids to examine")
args = parser.parse_args()

if not args.scopes: # If modifying these scopes, delete the file token.json.
    args.scopes = ["https://www.googleapis.com/auth/drive.readonly"]

creds = getCredentials(args.scopes, args.token, args.secret)

try:
    service = build('drive', 'v3', credentials=creds)

    for ident in args.id:
        cnt = 0
        params = dict(
                corpora="drive",
                driveId=ident,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                pageSize = 1000,
                fields = "nextPageToken, files(id)",
            )

        while True: # Loop over all the results calling the Drive v3 API
            results = service.files().list(**params).execute()
            pageToken = results.get("nextPageToken") 
            if pageToken is None: break # Last page
            params["pageToken"] = pageToken
            items = results.get('files', [])
            if not items: break # Past the end of the list
            print("nItems", len(items), cnt)
            cnt += len(items)
            if cnt > 5000: break
        print("Ident", ident, "count", cnt)
except HttpError as error:
    print(f'An error occurred: {error}')
