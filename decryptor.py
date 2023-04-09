import base64
import io
import json
import gnupg
import os

from datetime import datetime
from flask import Flask, request
from google.cloud import pubsub_v1
from google.cloud import secretmanager_v1
from google.cloud import storage

PROJECT_ID = os.environ.get('PROJECT_ID')
PRIVATE_KEY_SECRET_ID = os.environ.get('PRIVATE_KEY_SECRET_ID')


# docs: https://gnupg.readthedocs.io/en/latest/
# docs: https://gist.github.com/johnfedoruk/7f156d844af54cc91324dff4f54b11ce

def access_secret_version(project_id, secret_id, version_id):
    # Create the Secret Manager client
    client = secretmanager_v1.SecretManagerServiceClient()

    # Build the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version
    response = client.access_secret_version(request={"name": name})

    # Get the secret payload as a string
    secret_data = response.payload.data.decode("UTF-8")

    return secret_data


def read_gcs_file_to_string(bucket_name, source_blob_name):
    # Initialize the GCS client
    storage_client = storage.Client(project=PROJECT_ID)

    # Get the bucket
    bucket = storage_client.bucket(bucket_name)

    # Get the blob (file) from the bucket
    blob = bucket.blob(source_blob_name)

    # Read the file content as a string
    file_content = blob.download_as_text()

    return file_content


def upload_stringio_to_gcs(bucket_name, destination_blob_name, string_data):
    # Initialize the GCS client
    storage_client = storage.Client(project=PROJECT_ID)

    # Get the bucket
    bucket = storage_client.bucket(bucket_name)

    # Create a new blob in the bucket
    blob = bucket.blob(destination_blob_name)

    # Convert the StringIO object to a BytesIO object
    string_io = io.StringIO(string_data)
    bytes_io = io.BytesIO(string_io.getvalue().encode())

    # Upload the BytesIO object to the GCS bucket
    blob.upload_from_file(bytes_io)


def decrypt_from_gcs(bucket_name, source_blob_name):
    file_in_string = read_gcs_file_to_string(bucket_name, source_blob_name)
    decrypted_data = gpg.decrypt(file_in_string)

    return decrypted_data


# app = Flask(__name__)


# @app.route('/push-handlers/receive_messages', methods=['POST'])
# def pubsub_push():
#     envelope = json.loads(request.data.decode('utf-8'))
#     payload = base64.b64decode(envelope['message']['data'])
#
#     print(payload)
#
#     return 'OK', 200

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=8080, debug=True)

    # Initialize the GnuPG instance
    gpg = gnupg.GPG()
    # get private key from secret manager
    private_key = access_secret_version(project_id=PROJECT_ID, secret_id=PRIVATE_KEY_SECRET_ID, version_id=1)
    gpg.import_keys(key_data=private_key)
    # trusting imported key is important, or it will return an empty string as encrypted data
    gpg.trust_keys(fingerprints='71FEDB8B44D15B1AF199797A939B462CCE5D8DB8', trustlevel='TRUST_ULTIMATE')
    recipient = 'no-passwd@example.com'

    source_bucket_name = f'{PROJECT_ID}-demo-gpg-encrypted'
    source_blob_name = "gpg_demo_encrypted_2023-04-09_22-16-30.csv.gpg"

    decrypted_data = decrypt_from_gcs(source_bucket_name, source_blob_name)

    if not decrypted_data:
        raise RuntimeError('Cannot decrypt data...')

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destination_bucket_name = f'{PROJECT_ID}-demo-gpg-decrypted'
    destination_blob_name = f"gpg_demo_decrypted_{timestamp_str}.csv"

    upload_stringio_to_gcs(destination_bucket_name, destination_blob_name, str(decrypted_data))
