import xml.etree.ElementTree as ET

def xml_to_playlist(xml_content: str) -> dict:
    root = ET.fromstring(xml_content)
    
    tracks = []
    for track_elem in root.findall('track'):
        track = {
            'video_id': track_elem.find('video_id').text,
            'youtube_url': track_elem.find('youtube_url').text,
            'original_title': track_elem.find('original_title').text,
            'custom_title': track_elem.find('custom_title').text or "",
            'artist': track_elem.find('artist').text or "",
            'album': track_elem.find('album').text or "",
            'downloaded': track_elem.find('downloaded').text.lower() == 'true'
        }
        tracks.append(track)
    
    return {
        'playlist_id': root.get('id'),
        'playlist_url': root.get('url'),
        'tracks': tracks
    }
