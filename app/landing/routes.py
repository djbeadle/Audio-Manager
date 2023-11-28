from flask import redirect, render_template, Response, request, g, url_for
from app.landing import landing_bp
from db_operations import add_new_song, get_group_info, get_single_thing, get_song_counts, list_all_things, record_upload, search_for_song, search_for_things, get_next_asset_id, get_song_names, update_track, list_things_on_date, get_playlist, update_playlist

import db_operations as db_ops

import json, urllib
from uuid import UUID
from s3 import generate_presigned_post

@landing_bp.before_request
def translate_name():
    print(request.path)
    id = request.path.split('/')[1].lower()
    print(f'id: {id}')
    if id == 'ltbb':
        g.group_id = 0
    elif id == 'nice':
        g.group_id = 1
    elif id == '3rd': 
        g.group_id = 2
    elif id == 'm97ab':
        g.group_id = 3
    else:
        g.group_id = id

@landing_bp.route('/<raw_group_id>/search')
def search(raw_group_id):
    if request.args.get('tag'):
        return render_template(
            'search.html',
            group={'id': raw_group_id},
            things=search_for_things(request.args.get('tag', ''), g.group_id)
        )
    elif request.args.get('song'):
        return render_template(
            'search.html',
            group={'id': raw_group_id},
            things=search_for_song(request.args.get('song', ''), g.group_id)
        )
    else:
        return "Invalid search", 200


@landing_bp.route('/<raw_group_id>', methods=['GET'])
def home(raw_group_id):
    group_info = get_group_info(g.group_id)
    group_info = dict(zip(group_info.keys(), group_info))
    group_info['id'] = raw_group_id

    return render_template(
        'landing.html',
        group=group_info,
        song_counts=get_song_counts(g.group_id),
        things=list_all_things(g.group_id),
    )

@landing_bp.route('/<raw_group_id>/<record_date>', methods=['GET'])
def list_group_record_date(raw_group_id, record_date):
    group_info = get_group_info(g.group_id)
    group_info = dict(zip(group_info.keys(), group_info))
    group_info['id'] = raw_group_id

    return render_template(
        'landing.html',
        show_search=False,
        show_edit=False,
        group=group_info,
        song_counts=get_song_counts(g.group_id),
        things=list_things_on_date(g.group_id, record_date),
    )

@landing_bp.route('/<raw_group_id>/edit', methods=['GET'])
def edit(raw_group_id):

    ids_raw = map(lambda x: get_single_thing(x), request.args['filenames'].split(';'))
    id_dicts = []
    for id_raw in ids_raw:
        id = dict(id_raw)
        
        # Remove blank tags
        list_of_tags = [x for x in id['tags'].split(',') if x.strip() != '']

        if 'partial' in [x for x in list_of_tags]:
            list_of_tags.remove('partial')
            id['tags'] = ','.join(list_of_tags)
            id['partial'] = True
        else:
            id['partial'] = False
        id_dicts.append(id)

    return render_template(
        'edit.html',
        ids=id_dicts,
        group={ 'id': g.group_id },
        song_names=get_song_names(g.group_id)
    )

@landing_bp.route('/edit', methods=['POST'])
def save_edit():
    list(map(lambda x: update_track(**x), request.json))
    return '', 200


@landing_bp.route('/<raw_group_id>/track/<track_id>')
def track(raw_group_id, track_id):
    track_obj = get_single_thing(track_id)
    return render_template(
        "track.html",
        group={ 'id': g.group_id },
        track_obj=track_obj
    )

@landing_bp.route('/<raw_group_id>/songs')
def songs(raw_group_id):
    suggestions = get_song_names(raw_group_id)

    return render_template(
        "songs.html",
        group={ 'id': g.group_id },
        songs=suggestions
    )

@landing_bp.route('/<raw_group_id>/songs', methods=['POST'])
def create_song(raw_group_id):
    new_title = request.form['new-title'].strip()
    
    if add_new_song(g.group_id, new_title) == -1:
        return 'A song with this title already exists!', 304
    
    return redirect(url_for('landing_bp.songs', raw_group_id=raw_group_id))


@landing_bp.route('/info', methods=['GET'])
def info():
    text = 'This is the info route! Here is a kitten:'
    return render_template('info.html', content=text)


@landing_bp.route('/info', methods=['PUT'])
def update_info():
    return 'You have made a put request!'

@landing_bp.route('/<raw_group_id>/uploader')
def uploader(raw_group_id):
    return render_template(
        'uploader.html',
        group={ 'id': g.group_id },
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


@landing_bp.route('/<raw_group_id>/upload/s3/params', methods=['GET'])
def get_presigned_s3_upload_url(raw_group_id):
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
    filename_with_folder = f'{g.group_id}/{get_next_asset_id()}_{params["filename"].replace("+", " ")}'
    
    fields = {
        # 'x-amz-meta-uploader-name': uploader_name,
        'Content-Type': file_type,
        'Cache-Control': "public, max-age=31536000, immutable"
    }

    x = generate_presigned_post(filename_with_folder, params['type'], fields)
    # x['fields']['content_type'] = file_type
    return json.dumps(x)


@landing_bp.route('/playlist/<playlist_id>')
def get_playlist_route(playlist_id):
    playlist = get_playlist(playlist_id)
    playlist = dict(zip(playlist.keys(), playlist))

    tracks = [ db_ops.get_track(id) for id in playlist['tracks'].split(',')]
    return render_template('playlist.html', playlist_mode=True, tracks=tracks, playlist=playlist, group={'id': -1})
    # return json.dumps(list(get_playlist(playlist_id)))


@landing_bp.route('/playlist_edit/<playlist_id>')
def edit_playlist(playlist_id):
    playlist = get_playlist(playlist_id)
    playlist = dict(zip(playlist.keys(), playlist))

    tracks = [ db_ops.get_track(id) for id in playlist['tracks'].split(',')]
    return render_template('playlist_edit.html', playlist_mode=True, tracks=tracks, playlist=playlist, group={'id': -1}, playlist_id=playlist_id)

@landing_bp.post('/playlist_edit/<playlist_id>')
def save_playlist(playlist_id):
    updated_tracks = request.json['updated_tracks']
    update_playlist(playlist_id, updated_tracks)

    return redirect(url_for('landing_bp.edit_playlist', playlist_id=playlist_id))