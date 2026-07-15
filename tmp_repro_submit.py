import io
import requests
files = {'upload_file': ('test.wav', io.BytesIO(b'dummy'), 'audio/wav')}
data = {'language_mode': 'automatic', 'manual_language': ''}
try:
    r = requests.post('http://127.0.0.1:8000/process', files=files, data=data, timeout=30)
    print('status', r.status_code)
    print(r.text)
except Exception as e:
    print('ERR', repr(e))
