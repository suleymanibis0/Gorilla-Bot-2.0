import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def get_songs():

           
    playlist_url = "https://open.spotify.com/playlist/6a76lfZirHc8RROQWMDvEu?si=0978e20b27eb4c49"
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="5d2aa18bc5f648d2bbb4f6b9b80375fa", client_secret="89a9a36ea66d4988946e4f364fadf583"))
        # 1. İlk 100 şarkıyı iste
        results = sp.playlist_items(playlist_url)
        tracks = results['items']

        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])

        sarki_listesi = []
        
        for item in tracks:

            if item['track'] is not None:
                track = item['track']
                sarki_adi = track['name']
                # İlk sanatçıyı alıyoruz
                sanatci = track['artists'][0]['name'] 

                formatli_isim = f"{sanatci} - {sarki_adi}"
                sarki_listesi.append(formatli_isim)
        
        return sarki_listesi

    except Exception as e:
        return None