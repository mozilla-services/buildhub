# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import print_function

import boto3
import boto3.session
import os

AWS_REGION = "eu-central-1"
BUCKET_NAME = "buildhub-lambda"

FILENAME = "lambda.zip"

s3 = boto3.resource('s3', region_name=AWS_REGION)
try:
    s3.create_bucket(Bucket=BUCKET_NAME)
except:
    pass

print('Uploading %s to Amazon S3 bucket %s' % (FILENAME, BUCKET_NAME))
s3.Object(BUCKET_NAME, 'lambda.zip').put(Body=open(FILENAME, 'rb'))

print('File uploaded to https://s3.%s.amazonaws.com/%s/lambda.zip' %
      (AWS_REGION, BUCKET_NAME))
