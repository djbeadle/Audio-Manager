from flask import render_template, Response, request
from app.landing import landing_bp
from db_operations import list_all_things, record_upload, search_for_things

import json, urllib
from uuid import UUID
from s3 import generate_presigned_post

@landing_bp.route('/search')
def search():
    return render_template(
        'search.html',
        things=search_for_things(tag=request.args.get('tag', ''))
    )


@landing_bp.route('/', methods=['GET'])
def home():
    return render_template(
        'landing.html',
        things=list_all_things(),
    )

@landing_bp.route('/track/<track_name>')
def track(track_name):
    return render_template("track.html", track_name=track_name)


@landing_bp.route('/info', methods=['GET'])
def info():
    text = 'This is the info route! Here is a kitten:'
    return render_template('info.html', content=text)


@landing_bp.route('/info', methods=['PUT'])
def update_info():
    return 'You have made a put request!'

@landing_bp.route('/uploader')
def uploader():
    return render_template('uploader.html')


@landing_bp.route('/s3_upload_callback', methods = ['GET', 'POST', 'PUT'])
def sns():
    # TODO-Daniel: Verify Signature from Amazon to prevent malicious
    # AWS sends JSON with text/plain mimetype
    # TODO calculate e-tags client side and prevent duplicate uploads https://teppen.io/2018/06/23/aws_s3_etags/#what-is-an-s3-etag
    try:
        js = json.loads(request.data)
    except:
        pass

    hdr = request.headers.get('X-Amz-Sns-Message-Type', None)
    print(f'hdr: {hdr}')
    # subscribe to the SNS topic
    if hdr == 'SubscriptionConfirmation' and 'SubscribeURL' in js:
        # r = requests.get(js['SubscribeURL'])
        with urllib.request.urlopen(js['SubscribeURL']) as f:
            print(f.read().decode('utf-8'))

    if hdr == 'Notification':
        msg = js['Message']
        for r in json.loads(msg)['Records']:
            record_upload(
                r['s3']['object']['key'],
                r['eventTime'],
                # r['requestParameters']['sourceIPAddress'],
                r['s3']['object']['size'],
                r['s3']['object']['eTag'],
            )

    return 'OK\n'


@landing_bp.route('/upload/s3/params', methods=['GET'])
def get_presigned_s3_upload_url():
    # https://github.com/transloadit/uppy/blob/main/packages/%40uppy/companion/src/server/controllers/s3.js
    # TODO-prod: Keep tracing of the user_facing_ids and validate if this is in the database. For now just see if it's a valid UUID
    try:
        print(f'metadata: {json.dumps(request.args)}')

        uploader_name = request.args.get('metadata[uploader-name]')
        file_type = request.args.get('type')
    except ValueError as e:
        print(e)
        return Response({"error": "Now just hold on a minute, bucko."}, status=400, mimetype="application/json")

    params = request.args
    # TODO-Daniel: prepend unique numbers to filenames to prevent overwriting
    # Due to issues with how S3 encodes plus signs I'm just going to replace them with spaces for now.
    filename_with_folder = params["filename"].replace("+", " ")
    
    fields = {
        'x-amz-meta-uploader-name': uploader_name,
        'Content-Type': file_type,
        'Cache-Control': "public, max-age=31536000, immutable"
    }

    x = generate_presigned_post(filename_with_folder, params['type'], fields)
    # x['fields']['content_type'] = file_type
    return json.dumps(x)
