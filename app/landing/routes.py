from flask import redirect, render_template, Response, request
from app.landing import landing_bp
from db_operations import get_group_info, get_single_thing, get_song_counts, list_all_things, record_upload, search_for_song, search_for_things, get_next_asset_id, get_song_names, update_track

import json, urllib
from uuid import UUID
from s3 import generate_presigned_post

@landing_bp.route('/<int:group_id>/search')
def search(group_id):
    if request.args.get('tag'):
        return render_template(
            'search.html',
            group={'id': group_id},
            things=search_for_things(tag=request.args.get('tag', ''))
        )
    elif request.args.get('song'):
        return render_template(
            'search.html',
            group={'id': group_id},
            things=search_for_song(song=request.args.get('song', ''))
        )


@landing_bp.route('/<int:group_id>', methods=['GET'])
def home(group_id):
    return render_template(
        'landing.html',
        group=get_group_info(group_id),
        song_counts=get_song_counts(),
        things=list_all_things(group_id),
    )

@landing_bp.route('/<int:group_id>/edit', methods=['GET'])
def edit(group_id):
    return render_template(
        'edit.html',
        ids=map(lambda x: get_single_thing(x), request.args['filenames'].split(';')),
        group={ 'id': group_id },
        song_names=get_song_names()
    )

@landing_bp.route('/edit', methods=['POST'])
def save_edit():
    list(map(lambda x: update_track(**x), request.json))
    return '', 200

@landing_bp.route('/<int:group_id>/track/<track_id>')
def track(group_id, track_id):
    track_obj = get_single_thing(track_id)
    return render_template(
        "track.html",
        group={ 'id': group_id },
        track_obj=track_obj
    )


@landing_bp.route('/info', methods=['GET'])
def info():
    text = 'This is the info route! Here is a kitten:'
    return render_template('info.html', content=text)


@landing_bp.route('/info', methods=['PUT'])
def update_info():
    return 'You have made a put request!'

@landing_bp.route('/<int:group_id>/uploader')
def uploader(group_id):
    return render_template(
        'uploader.html',
        group={ 'id': group_id },
    )


@landing_bp.route('/s3_upload_callback', methods = ['GET', 'POST', 'PUT'])
def sns():
    # TODO-Daniel: Verify Signature from Amazon to prevent malicious
    # AWS sends JSON with text/plain mimetype
    # TODO calculate e-tags client side and prevent duplicate uploads https://teppen.io/2018/06/23/aws_s3_etags/#what-is-an-s3-etag
    try:
        js = json.loads(request.data)
    except Exception as e:
        print("ERROR: An error occurred while parsing an SNS from Amazon! \n", e)

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
            folder, file = r['s3']['object']['key'].split('/')

            record_upload(
                file,
                r['eventTime'],
                # r['requestParameters']['sourceIPAddress'],
                r['s3']['object']['size'],
                r['s3']['object']['eTag'],
                folder
            )

    return 'OK\n'


@landing_bp.route('/<int:group_id>/upload/s3/params', methods=['GET'])
def get_presigned_s3_upload_url(group_id):
    # https://github.com/transloadit/uppy/blob/main/packages/%40uppy/companion/src/server/controllers/s3.js
    # TODO-prod: Keep tracing of the user_facing_ids and validate if this is in the database. For now just see if it's a valid UUID
    try:
        print(f'metadata: {json.dumps(request.args)}')

        # uploader_name = request.args.get('metadata[uploader-name]')
        file_type = request.args.get('type')
    except ValueError as e:
        print(e)
        return Response({"error": "Now just hold on a minute, bucko."}, status=400, mimetype="application/json")

    params = request.args
    # Due to issues with how S3 encodes plus signs I'm just going to replace them with spaces for now.
    filename_with_folder = f'{group_id}/{get_next_asset_id()}_{params["filename"].replace("+", " ")}'
    
    fields = {
        # 'x-amz-meta-uploader-name': uploader_name,
        'Content-Type': file_type,
        'Cache-Control': "public, max-age=31536000, immutable"
    }

    x = generate_presigned_post(filename_with_folder, params['type'], fields)
    # x['fields']['content_type'] = file_type
    return json.dumps(x)
