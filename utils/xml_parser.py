# utils/xml_parser.py
import xml.etree.ElementTree as ET
from utils.bot_storage import bot_storage

def xml_to_playlist(xml_content: str) -> dict:
    root = ET.fromstring(xml_content)

    tracks = []
    for track_elem in root.findall('track'):
        # Safe element finding with default values
        video_id_elem = track_elem.find('video_id')
        youtube_url_elem = track_elem.find('youtube_url')
        original_title_elem = track_elem.find('original_title')
        custom_title_elem = track_elem.find('custom_title')
        artist_elem = track_elem.find('artist')
        album_elem = track_elem.find('album')
        downloaded_elem = track_elem.find('downloaded')
        
        track = {
            'video_id': video_id_elem.text if video_id_elem is not None and video_id_elem.text else "",
            'youtube_url': youtube_url_elem.text if youtube_url_elem is not None and youtube_url_elem.text else "",
            'original_title': original_title_elem.text if original_title_elem is not None and original_title_elem.text else "",
            'custom_title': custom_title_elem.text if custom_title_elem is not None and custom_title_elem.text else "",
            'artist': artist_elem.text if artist_elem is not None and artist_elem.text else "",
            'album': album_elem.text if album_elem is not None and album_elem.text else "",
            'downloaded': downloaded_elem.text.lower() == 'true' if downloaded_elem is not None and downloaded_elem.text else False
        }
        tracks.append(track)

    return {
        'playlist_id': root.get('id', ''),
        'playlist_url': root.get('url', ''),
        'last_updated': root.get('last_updated', ''),
        'tracks': tracks
    }

def merge_playlist_data(current_data: dict, uploaded_data: dict) -> dict:
    """
    Merge uploaded XML data with current playlist data
    Preserves video_id and youtube_url from current data, takes metadata from uploaded
    """
    merged_data = current_data.copy()
    
    # Create a map of uploaded tracks by video_id for quick lookup
    uploaded_tracks_map = {track['video_id']: track for track in uploaded_data['tracks']}
    
    merged_tracks = []
    
    for current_track in current_data['tracks']:
        video_id = current_track['video_id']
        
        if video_id in uploaded_tracks_map:
            # Merge: keep current video_id and youtube_url, take metadata from uploaded
            uploaded_track = uploaded_tracks_map[video_id]
            merged_track = {
                'video_id': current_track['video_id'],
                'youtube_url': current_track['youtube_url'],
                'original_title': current_track['original_title'],
                'custom_title': uploaded_track.get('custom_title', current_track.get('original_title', '')),
                'artist': uploaded_track.get('artist', ''),
                'album': uploaded_track.get('album', ''),
                'downloaded': uploaded_track.get('downloaded', False)
            }
        else:
            # Track exists in current but not in uploaded - use current data
            merged_track = current_track.copy()
        
        merged_tracks.append(merged_track)
    
    merged_data['tracks'] = merged_tracks
    return merged_data

def compare_playlists(current_playlist: dict, stored_playlist: dict) -> dict:
    """
    Compare current playlist with stored version and return:
    - new_tracks: Tracks that don't exist in stored version
    - updated_tracks: Tracks that exist but might have changes
    """
    if not stored_playlist:
        return {
            'new_tracks': current_playlist['tracks'],
            'updated_tracks': [],
            'unchanged_tracks': []
        }
    
    # Create a map of stored tracks by video_id for quick lookup
    stored_tracks_map = {track['video_id']: track for track in stored_playlist['tracks']}
    
    new_tracks = []
    updated_tracks = []
    unchanged_tracks = []
    
    for current_track in current_playlist['tracks']:
        video_id = current_track['video_id']
        
        if video_id not in stored_tracks_map:
            # This is a completely new track
            new_tracks.append(current_track)
        else:
            stored_track = stored_tracks_map[video_id]
            
            # Check if metadata has changed
            metadata_changed = (
                current_track.get('custom_title') != stored_track.get('custom_title') or
                current_track.get('artist') != stored_track.get('artist') or
                current_track.get('album') != stored_track.get('album') or
                current_track.get('original_title') != stored_track.get('original_title')
            )
            
            if metadata_changed:
                # Keep the downloaded status from stored version
                updated_track = current_track.copy()
                updated_track['downloaded'] = stored_track['downloaded']
                updated_tracks.append(updated_track)
            else:
                # Track is unchanged, keep stored download status
                unchanged_tracks.append(stored_track)
    
    return {
        'new_tracks': new_tracks,
        'updated_tracks': updated_tracks,
        'unchanged_tracks': unchanged_tracks
    }

def get_tracks_to_download(user_id: int, current_playlist: dict) -> list:
    """Get list of tracks that need to be downloaded - ONLY NON-DOWNLOADED ONES"""
    # Try to load bot's stored XML
    stored_xml = bot_storage.load_playlist_xml(user_id, current_playlist['playlist_id'])

    if not stored_xml:
        print("DEBUG: No stored XML found - all tracks need download")
        # No stored version, all tracks need download but mark them as not downloaded
        for track in current_playlist['tracks']:
            track['downloaded'] = False
        return current_playlist['tracks']

    stored_playlist = xml_to_playlist(stored_xml)
    comparison = compare_playlists(current_playlist, stored_playlist)

    print(f"DEBUG: Comparison results - New: {len(comparison['new_tracks'])}, Updated: {len(comparison['updated_tracks'])}, Unchanged: {len(comparison['unchanged_tracks'])}")

    # Return ONLY tracks that are NOT downloaded
    tracks_to_download = []

    # New tracks - not in stored version, so not downloaded
    for track in comparison['new_tracks']:
        track['downloaded'] = False  # Ensure they're marked as not downloaded
        tracks_to_download.append(track)
        print(f"DEBUG: New track - {track.get('custom_title') or track['original_title']}")

    # Updated tracks - only if not downloaded
    for track in comparison['updated_tracks']:
        if not track.get('downloaded', False):
            tracks_to_download.append(track)
            print(f"DEBUG: Updated track (not downloaded) - {track.get('custom_title') or track['original_title']}")
        else:
            print(f"DEBUG: Updated track (SKIPPING - already downloaded) - {track.get('custom_title') or track['original_title']}")

    # Unchanged tracks - only if not downloaded
    for track in comparison['unchanged_tracks']:
        if not track.get('downloaded', False):
            tracks_to_download.append(track)
            print(f"DEBUG: Unchanged track (not downloaded) - {track.get('custom_title') or track['original_title']}")
        else:
            print(f"DEBUG: Unchanged track (SKIPPING - already downloaded) - {track.get('custom_title') or track['original_title']}")

    print(f"DEBUG: Total tracks to download: {len(tracks_to_download)}")
    return tracks_to_download
