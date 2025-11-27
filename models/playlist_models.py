from dataclasses import dataclass, asdict
from typing import List, Optional
import json

@dataclass
class Track:
    video_id: str
    youtube_url: str
    original_title: str
    custom_title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    downloaded: bool = False
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class Playlist:
    playlist_id: str
    playlist_url: str
    tracks: List[Track]
    last_checked: str = None
    
    def to_dict(self):
        return {
            'playlist_id': self.playlist_id,
            'playlist_url': self.playlist_url,
            'tracks': [track.to_dict() for track in self.tracks],
            'last_checked': self.last_checked
        }
    
    @classmethod
    def from_dict(cls, data):
        tracks = [Track.from_dict(track_data) for track_data in data['tracks']]
        return cls(
            playlist_id=data['playlist_id'],
            playlist_url=data['playlist_url'],
            tracks=tracks,
            last_checked=data.get('last_checked')
        )
