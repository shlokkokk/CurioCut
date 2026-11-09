"""YouTube Shorts Uploader Module.
Uploads an MP4 video to YouTube using the authenticated credentials in youtube_token.json.
Automatically optimizes the title, description, and tags for YouTube Shorts.
"""
import os
import sys
import json
import time
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_FILE = 'youtube_token.json'
CLIENT_SECRET_FILE = 'client_secret.json'

def get_authenticated_service():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"Missing {TOKEN_FILE}! Run authenticate_youtube.py first.")
    
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
    
    creds = Credentials.from_authorized_user_info(token_data)
    
    # Auto-refresh expired token using refresh_token
    if creds.expired and creds.refresh_token:
        print("Refreshing expired access token...")
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
            
    return build('youtube', 'v3', credentials=creds)

def upload_short(video_path, title, description="", tags=None, privacy_status="public"):
    """Uploads a video to YouTube as a Short.
    
    Args:
        video_path (str): Path to the .mp4 file
        title (str): Video title
        description (str): Video description
        tags (list): List of hashtag strings
        privacy_status (str): 'public', 'unlisted', or 'private'
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    youtube = get_authenticated_service()
    
    # Ensure #shorts is in title or description so YouTube tags it as a Short
    if "#shorts" not in title.lower() and "#shorts" not in description.lower():
        title = f"{title} #shorts"
        
    if not tags:
        tags = ["shorts", "viral", "curiocut", "animation", "truestory", "history", "funfacts"]

    body = {
        'snippet': {
            'title': title[:100],
            'description': description + "\n\n#shorts #animation #facts #curiocut",
            'tags': tags,
            'categoryId': '27' # 27 = Education, 23 = Comedy, 24 = Entertainment
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    print(f"\nUploading to YouTube Shorts: '{title}'...")
    print(f"File size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    
    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True, chunksize=1024*1024*5)
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%...")
            
    video_id = response.get('id')
    video_url = f"https://youtube.com/shorts/{video_id}"
    print("\n" + "="*60)
    print(f"SUCCESSFULLY UPLOADED TO YOUTUBE SHORTS!")
    print(f"Video URL: {video_url}")
    print("="*60 + "\n")
    return video_id, video_url

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python youtube_uploader.py <path_to_video.mp4> [title] [privacy_status]")
        sys.exit(1)
        
    v_path = sys.argv[1]
    v_title = sys.argv[2] if len(sys.argv) > 2 else "The Girl Who Was Mailed To Grandma"
    v_privacy = sys.argv[3] if len(sys.argv) > 3 else "unlisted"
    
    upload_short(v_path, v_title, privacy_status=v_privacy)

