import base64
import io
import json
import gnupg
import os

from datetime import datetime
from flask import Flask, request
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


app = Flask(__name__)
# Initialize the GnuPG instance
gpg = gnupg.GPG()
# get private key from secret manager
private_key = access_secret_version(project_id=PROJECT_ID, secret_id=PRIVATE_KEY_SECRET_ID, version_id=1)
gpg.import_keys(key_data=private_key)
# trusting imported key is important, or it will return an empty string as encrypted data
gpg.trust_keys(fingerprints=os.environ.get('GPG_KEY_FINGERPRINTS'), trustlevel='TRUST_ULTIMATE')
# set recipient which is required to decrypt
recipient = os.environ.get('GPG_RECIPIENT')


@app.route('/push-handlers/receive_messages', methods=['POST'])
def pubsub_push():
    envelope = json.loads(request.data.decode('utf-8'))
    event_type = envelope['message']['attributes']['eventType']
    if event_type != 'OBJECT_FINALIZE':
        return 'Is not object finalise event, ignore', 204

    payload = json.loads(base64.b64decode(envelope['message']['data']))
    source_bucket_name = payload['bucket']
    source_blob_name = payload['name']

    decrypted_data = decrypt_from_gcs(source_bucket_name, source_blob_name)

    if not decrypted_data:
        raise RuntimeError('Cannot decrypt data...')  # consider implement a dead letter queue for this

    now = datetime.now()
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destination_bucket_name = os.environ.get('DESTINATION_BUCKET_NAME')
    destination_blob_name, _ = os.path.splitext(source_blob_name)
    destination_blob_name_with_timestamp = f"{destination_blob_name}_{timestamp_str}.csv"

    upload_stringio_to_gcs(destination_bucket_name, destination_blob_name_with_timestamp, str(decrypted_data))

    return 'OK', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
