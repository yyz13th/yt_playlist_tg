import json
import os

PLAYLIST_STORAGE_FILE = 'playlist_storage.json'

def load_playlist_storage():
    if os.path.exists(PLAYLIST_STORAGE_FILE):
        with open(PLAYLIST_STORAGE_FILE, "r", encoding='utf-8') as file:
            data = json.load(file)
            # Convert back to Playlist objects
            return {k: Playlist.from_dict(v) for k, v in data.items()}
    return {}

def save_playlist_storage(data):
    # Convert Playlist objects to dict
    dict_data = {k: v.to_dict() for k, v in data.items()}
    with open(PLAYLIST_STORAGE_FILE, "w", encoding='utf-8') as file:
        json.dump(dict_data, file, ensure_ascii=False, indent=2)

# Global playlist storage
playlist_storage = load_playlist_storage()
