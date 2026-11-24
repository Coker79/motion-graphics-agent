#!/usr/bin/env python3
"""YouTube Data API helper for The Efficiency Edge.

Secrets live OUTSIDE the repo in ~/.config/efficiency-edge/ (client.json, token.json, chmod 600).
If token.json is missing or the refresh token expired (Testing-mode apps: 7 days),
run `python3 tools/yt.py login` and approve the code at google.com/device.

Usage:
  yt.py login
  yt.py me
  yt.py upload FILE.mp4 --title T --desc-file D.txt [--tags a,b] [--publish-at 2026-11-28T20:00:00Z] [--privacy private|unlisted|public] [--category 27]
  yt.py thumbnail VIDEO_ID image.jpg
  yt.py captions VIDEO_ID subs.srt [--lang en] [--name English]
  yt.py update VIDEO_ID [--title T] [--desc-file D.txt] [--tags a,b] [--publish-at ISO]
  yt.py get VIDEO_ID
  yt.py delete VIDEO_ID --yes
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, uuid

CFG = os.path.expanduser('~/.config/efficiency-edge')
FULL = os.path.join(CFG, 'token-full.json')  # Desktop-client sign-in: youtube + force-ssl (captions) + analytics
if os.path.exists(FULL):
    CLIENT, TOKEN = os.path.join(CFG, 'client-desktop.json'), FULL
else:
    CLIENT, TOKEN = os.path.join(CFG, 'client.json'), os.path.join(CFG, 'token.json')
API = 'https://www.googleapis.com'


def _write_secret(path, obj):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.write(fd, json.dumps(obj).encode()); os.close(fd)


def _post_form(url, fields):
    try:
        return json.load(urllib.request.urlopen(url, urllib.parse.urlencode(fields).encode()))
    except urllib.error.HTTPError as e:
        raise SystemExit(f'{url} -> {e.code} {e.read().decode()[:400]}')


def client():
    return json.load(open(CLIENT))['installed']


def login():
    c = client()
    d = _post_form('https://oauth2.googleapis.com/device/code', {'client_id': c['client_id'], 'scope': f'{API}/auth/youtube'})
    print(f"Open {d['verification_url']} and enter code {d['user_code']} (expires in {d['expires_in']//60} min)", flush=True)
    iv, end = d.get('interval', 5), time.time() + d['expires_in']
    while time.time() < end:
        time.sleep(iv)
        try:
            t = json.load(urllib.request.urlopen('https://oauth2.googleapis.com/token', urllib.parse.urlencode({
                'client_id': c['client_id'], 'client_secret': c['client_secret'], 'device_code': d['device_code'],
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'}).encode()))
            t['obtained_at'] = int(time.time()); _write_secret(TOKEN, t); print('Signed in.'); return
        except urllib.error.HTTPError as e:
            err = json.loads(e.read().decode()).get('error')
            if err == 'slow_down': iv += 5
            elif err != 'authorization_pending': raise SystemExit('login failed: ' + err)
    raise SystemExit('code expired')


def token():
    if not os.path.exists(TOKEN): raise SystemExit('Not signed in: run `yt.py login`.')
    t = json.load(open(TOKEN))
    if time.time() > t['obtained_at'] + t.get('expires_in', 3600) - 120:
        c = client()
        n = _post_form('https://oauth2.googleapis.com/token', {'client_id': c['client_id'], 'client_secret': c['client_secret'],
                                                               'refresh_token': t['refresh_token'], 'grant_type': 'refresh_token'})
        t.update(n); t['obtained_at'] = int(time.time()); _write_secret(TOKEN, t)
    return t['access_token']


def req(method, path, body=None, headers=None, raw=None):
    h = {'Authorization': 'Bearer ' + token()}
    if body is not None: h['Content-Type'] = 'application/json'; raw = json.dumps(body).encode()
    h.update(headers or {})
    r = urllib.request.Request(path if path.startswith('http') else API + path, data=raw, method=method, headers=h)
    try:
        resp = urllib.request.urlopen(r)
        txt = resp.read().decode(); return (json.loads(txt) if txt else {}), resp.headers
    except urllib.error.HTTPError as e:
        raise SystemExit(f'{method} {path} -> {e.code} {e.read().decode()[:600]}')


def upload(a):
    meta = {'snippet': {'title': a.title, 'description': open(a.desc_file).read() if a.desc_file else '',
                        'tags': a.tags.split(',') if a.tags else [], 'categoryId': str(a.category)},
            'status': {'privacyStatus': 'private' if a.publish_at else a.privacy, 'selfDeclaredMadeForKids': False}}
    if a.publish_at: meta['status']['publishAt'] = a.publish_at
    size = os.path.getsize(a.file)
    _, hd = req('POST', '/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status', body=meta,
                headers={'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(size)})
    loc = hd['Location']
    r = urllib.request.Request(loc, data=open(a.file, 'rb').read(), method='PUT',
                               headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'video/mp4'})
    v = json.load(urllib.request.urlopen(r))
    print(json.dumps({'id': v['id'], 'url': 'https://www.youtube.com/watch?v=' + v['id'], 'status': v['status']}))


def multipart(meta, data, mime):
    b = uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{json.dumps(meta)}\r\n'
            f'--{b}\r\nContent-Type: {mime}\r\n\r\n').encode() + data + f'\r\n--{b}--'.encode()
    return body, {'Content-Type': f'multipart/related; boundary={b}'}


def main():
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('login'); s.add_parser('me')
    u = s.add_parser('upload'); u.add_argument('file'); u.add_argument('--title', required=True); u.add_argument('--desc-file')
    u.add_argument('--tags'); u.add_argument('--publish-at'); u.add_argument('--privacy', default='private'); u.add_argument('--category', default=27)
    t = s.add_parser('thumbnail'); t.add_argument('video'); t.add_argument('image')
    c = s.add_parser('captions'); c.add_argument('video'); c.add_argument('srt'); c.add_argument('--lang', default='en'); c.add_argument('--name', default='English')
    up = s.add_parser('update'); up.add_argument('video'); up.add_argument('--title'); up.add_argument('--desc-file'); up.add_argument('--tags'); up.add_argument('--publish-at')
    g = s.add_parser('get'); g.add_argument('video')
    de = s.add_parser('delete'); de.add_argument('video'); de.add_argument('--yes', action='store_true')
    an = s.add_parser('analytics'); an.add_argument('--start', default='2026-10-25'); an.add_argument('--end', default='2026-11-23'); an.add_argument('--dims', default='video'); an.add_argument('--metrics', default='views,estimatedMinutesWatched,averageViewPercentage,subscribersGained')
    a = p.parse_args()
    if a.cmd == 'login': return login()
    if a.cmd == 'me':
        d, _ = req('GET', '/youtube/v3/channels?part=snippet,statistics&mine=true')
        for i in d['items']: print(i['id'], i['snippet']['title'], i['statistics'])
    elif a.cmd == 'upload': upload(a)
    elif a.cmd == 'thumbnail':
        mime = 'image/png' if a.image.endswith('.png') else 'image/jpeg'
        d, _ = req('POST', f'/upload/youtube/v3/thumbnails/set?videoId={a.video}', raw=open(a.image, 'rb').read(), headers={'Content-Type': mime})
        print('thumbnail set:', list(d.get('items', [{}])[0].get('default', {}).values())[:1])
    elif a.cmd == 'captions':
        body, hd = multipart({'snippet': {'videoId': a.video, 'language': a.lang, 'name': a.name, 'isDraft': False}}, open(a.srt, 'rb').read(), 'application/octet-stream')
        d, _ = req('POST', '/upload/youtube/v3/captions?uploadType=multipart&part=snippet', raw=body, headers=hd)
        print('captions added:', d.get('id'))
    elif a.cmd == 'analytics':
        q = urllib.parse.urlencode({'ids': 'channel==MINE', 'startDate': a.start, 'endDate': a.end, 'metrics': a.metrics, 'dimensions': a.dims, 'sort': '-views', 'maxResults': 25} if a.dims == 'video' else {'ids': 'channel==MINE', 'startDate': a.start, 'endDate': a.end, 'metrics': a.metrics, 'dimensions': a.dims})
        d, _ = req('GET', 'https://youtubeanalytics.googleapis.com/v2/reports?' + q)
        print([h['name'] for h in d['columnHeaders']])
        for r in d.get('rows', []): print(r)
    elif a.cmd == 'get':
        d, _ = req('GET', f'/youtube/v3/videos?part=snippet,status&id={a.video}')
        i = d['items'][0]; print(json.dumps({'title': i['snippet']['title'], 'status': i['status']}, indent=1))
    elif a.cmd == 'delete':
        if not a.yes: raise SystemExit('refusing without --yes')
        req('DELETE', f'/youtube/v3/videos?id={a.video}'); print('deleted:', a.video)
    elif a.cmd == 'update':
        d, _ = req('GET', f'/youtube/v3/videos?part=snippet,status&id={a.video}'); i = d['items'][0]
        sn, st = i['snippet'], i['status']
        if a.title: sn['title'] = a.title
        if a.desc_file: sn['description'] = open(a.desc_file).read()
        if a.tags: sn['tags'] = a.tags.split(',')
        if a.publish_at: st['privacyStatus'] = 'private'; st['publishAt'] = a.publish_at
        keep = {k: sn[k] for k in ('title', 'description', 'tags', 'categoryId', 'defaultLanguage') if k in sn}
        d, _ = req('PUT', '/youtube/v3/videos?part=snippet,status', body={'id': a.video, 'snippet': keep,
                   'status': {k: st[k] for k in ('privacyStatus', 'publishAt', 'selfDeclaredMadeForKids', 'embeddable', 'license', 'publicStatsViewable') if k in st}})
        print('updated:', d.get('id'))


if __name__ == '__main__':
    main()
