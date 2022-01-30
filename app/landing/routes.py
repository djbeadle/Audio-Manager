from flask import render_template, Response, request
from app.landing import landing_bp
from db_operations import list_all_things, record_upload

import json, urllib

@landing_bp.route('/', methods=['GET'])
def home():
    text = 'This is the landing route!'
    return render_template(
        'landing.html',
        things=list_all_things(),
        content=text
    )


@landing_bp.route('/info', methods=['GET'])
def info():
    text = 'This is the info route! Here is a kitten:'
    return render_template('info.html', content=text)


@landing_bp.route('/info', methods=['PUT'])
def update_info():
    return 'You have made a put request!'



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
                r['awsRegion'],
                # r['requestParameters']['sourceIPAddress'],
                r['s3']['object']['size'],
                r['s3']['object']['eTag'],
            )

    return 'OK\n'

