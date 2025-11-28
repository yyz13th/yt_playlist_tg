# utils/xml_generator.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
from utils.bot_storage import bot_storage

def playlist_to_xml(playlist_data: dict, user_id: int = None) -> str:
    """
    Generate XML from playlist data, copying from existing bot XML if available
    """
    root = ET.Element('playlist')
    root.set('id', str(playlist_data.get('playlist_id', '')))
    root.set('url', str(playlist_data.get('playlist_url', '')))
    root.set('last_updated', str(playlist_data.get('last_updated', '')))

    tracks = playlist_data.get('tracks', [])
    print(f"📊 Generating XML for {len(tracks)} tracks")

    # Try to load existing bot XML to copy metadata and download flags
    existing_tracks_map = {}
    if user_id:
        existing_xml = bot_storage.load_playlist_xml(user_id, playlist_data['playlist_id'])
        if existing_xml:
            from utils.xml_parser import xml_to_playlist
            existing_playlist = xml_to_playlist(existing_xml)
            existing_tracks_map = {track['video_id']: track for track in existing_playlist['tracks']}

    for track in tracks:
        track_elem = ET.SubElement(root, 'track')

        # Helper function to safely create elements with text
        def create_element(parent, tag, text):
            elem = ET.SubElement(parent, tag)
            elem.text = str(text) if text is not None else ''
            return elem

        video_id = track.get('video_id', '')
        
        # Check if we have existing data for this track
        existing_track = existing_tracks_map.get(video_id)

        # Create all elements, preferring existing metadata when available
        create_element(track_elem, 'video_id', video_id)
        create_element(track_elem, 'youtube_url', track.get('youtube_url', ''))
        create_element(track_elem, 'original_title', track.get('original_title', ''))
        
        # Use existing custom_title if available, otherwise use current
        if existing_track and existing_track.get('custom_title'):
            custom_title = existing_track['custom_title']
        else:
            custom_title = track.get('custom_title', track.get('original_title', ''))
        create_element(track_elem, 'custom_title', custom_title)
        
        # Use existing artist/album if available
        if existing_track:
            artist = existing_track.get('artist', '')
            album = existing_track.get('album', '')
        else:
            artist = track.get('artist', '')
            album = track.get('album', '')
        create_element(track_elem, 'artist', artist)
        create_element(track_elem, 'album', album)
        
        # Use existing download flag if available, otherwise default to false
        if existing_track:
            downloaded = str(existing_track.get('downloaded', False)).lower()
        else:
            downloaded = 'false'
        create_element(track_elem, 'downloaded', downloaded)

    # Convert to string and pretty print
    rough_string = ET.tostring(root, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Ensure proper XML declaration
    if pretty_xml.startswith('<?xml version="1.0" ?>'):
        return pretty_xml
    else:
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml

def save_bot_xml(user_id: int, playlist_data: dict) -> str:
    """Save bot's internal XML with download tracking"""
    # For bot's internal version, we want to mark newly downloaded tracks as true
    # but preserve existing download flags
    xml_content = playlist_to_xml(playlist_data, user_id)
    return bot_storage.save_playlist_xml(user_id, playlist_data['playlist_id'], xml_content)
