import xml.etree.ElementTree as ET
from xml.dom import minidom

def playlist_to_xml(playlist_data: dict) -> str:
    root = ET.Element('playlist')
    root.set('id', playlist_data['playlist_id'])
    root.set('url', playlist_data['playlist_url'])
    
    tracks = playlist_data.get('tracks', [])
    print(f"📊 Generating XML for {len(tracks)} tracks")
    
    for track in tracks:
        track_elem = ET.SubElement(root, 'track')
        
        # Use proper text content, not self-closing tags
        video_id_elem = ET.SubElement(track_elem, 'video_id')
        video_id_elem.text = track['video_id']
        
        youtube_url_elem = ET.SubElement(track_elem, 'youtube_url')
        youtube_url_elem.text = track['youtube_url']
        
        original_title_elem = ET.SubElement(track_elem, 'original_title')
        original_title_elem.text = track['original_title']
        
        custom_title_elem = ET.SubElement(track_elem, 'custom_title')
        custom_title_elem.text = track.get('custom_title', track['original_title'])
        
        artist_elem = ET.SubElement(track_elem, 'artist')
        artist_elem.text = track.get('artist', '')
        
        album_elem = ET.SubElement(track_elem, 'album')
        album_elem.text = track.get('album', '')
        
        downloaded_elem = ET.SubElement(track_elem, 'downloaded')
        downloaded_elem.text = str(track.get('downloaded', False)).lower()
    
    # Pretty print with proper XML declaration
    rough_string = ET.tostring(root, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    
    # Return with proper XML declaration
    return reparsed.toprettyxml(indent="  ")
