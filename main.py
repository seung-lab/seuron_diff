import json
import requests
from flask import Flask, make_response, redirect

app = Flask(__name__)

@app.route
def home():
    resp = make_response()
    resp.headers['Access-Control-Allow-Origin'] = '*'
    acah = "Origin, X-Requested-With, Content-Type, Accept"
    resp.headers["Access-Control-Allow-Headers"] = acah
    resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    resp.headers["Connection"] = "keep-alive"
    return resp

@app.route('/')
def get_diffs():
    from google.cloud import storage
    import os
    bucket_name = os.environ["BUCKET_NAME"]
    print(bucket_name)
    prefix = "diff"
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    msg = """<p>Diffs for volume:"""
    blobs = bucket.list_blobs(prefix=prefix)
    for b in blobs:
        if not b.name.endswith('.json'):
            continue
        else:
            segname = b.name[len(prefix)+1:-5]
            url = str(segname)
            msg += """<p>
<a href={}>{}</a></p>
""".format(url, segname)
    return msg

@app.route('/<name>')
def get_segpair_default(name):
    return get_segpair(name, 200)

@app.route('/<name>/<limit>')
def get_segpair_limit(name,limit):
    return get_segpair(name, int(limit))

def get_segpair(name,limit):
    from cloudfiles import CloudFiles
    from copy import deepcopy
    import urllib
    import os
    bucket_name = os.environ["BUCKET_NAME"]
    gs_path = "gs://"+os.path.join(bucket_name, "diff")
    msg = """<p>Segment pairs differ significantly</p>"""
    storage = CloudFiles(gs_path)
    data = storage.get_json(name+'.json')
    ng_host = data.get('ng_host', "neuromancer-seung-import.appspot.com")
    ng_payload = data['ng_payload']

    if len(data['seg_pairs']) < limit:
        limit = len(data['seg_pairs'])
    for i, p in enumerate(data['seg_pairs'][:limit]):
        payload = deepcopy(ng_payload)

        payload['layers']['seg']['objectAlpha'] = 0.99
        payload['layers']['seg']['segments'] = [str(p['seg_id'])]
        payload['layers']['seg']['segmentColors'] = {str(p['seg_id']): "#ff0000"}
        if 'gt' in payload['layers']:
            payload['layers']['gt']['objectAlpha'] = 0.99
            payload['layers']['gt']['segments'] = [str(p['gt_id'])]
            payload['layers']['gt']['segmentColors'] = {str(p['gt_id']): "#00ffff"}
        url = "https://{}/#!{}".format(ng_host, urllib.parse.quote(json.dumps(payload)))
        msg += """<p>
<a href={url} target="_blank">{idx}. {s1} ({size1}), {s2} ({size2})</a></p>""".format(
            idx=i,
            url=url,
            s1=p['seg_id'],
            size1=p['seg_size'],
            s2=p['gt_id'],
            size2=p['gt_size'],
        )
    return msg

print("diff server started")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

