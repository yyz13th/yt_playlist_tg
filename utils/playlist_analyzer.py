import yt_dlp

async def analyze_playlist(playlist_url: str):
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        
        tracks = []
        for entry in info['entries']:
            if entry:  # Some entries might be None
                track = {
                    'video_id': entry['id'],
                    'youtube_url': entry['url'],
                    'original_title': entry['title'],
                    'custom_title': entry['title'],  # Default to original
                    'artist': "",
                    'album': "",
                    'downloaded': False
                }
                tracks.append(track)
        
        return {
            'playlist_id': info['id'],
            'playlist_url': playlist_url,
            'tracks': tracks
        }
