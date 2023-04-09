import csv
import io
import os
import gnupg
import random
import string

from datetime import datetime
from google.cloud import secretmanager_v1
from google.cloud import storage

PROJECT_ID = os.environ.get('PROJECT_ID')
PUBLIC_KEY_SECRET_ID = os.environ.get('PUBLIC_KEY_SECRET_ID')


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


def upload_stringio_to_gcs(bucket_name, destination_blob_name, string_data):
    # Initialize the GCS client
    storage_client = storage.Client()

    # Get the bucket
    bucket = storage_client.bucket(bucket_name)

    # Create a new blob in the bucket
    blob = bucket.blob(destination_blob_name)

    # Convert the StringIO object to a BytesIO object
    string_io = io.StringIO(string_data)
    bytes_io = io.BytesIO(string_io.getvalue().encode())

    # Upload the BytesIO object to the GCS bucket
    blob.upload_from_file(bytes_io)


def generate_in_memory_csv():
    def random_string(length):
        return ''.join(random.choice(string.ascii_letters) for _ in range(length))

    long_dict = {f"key{i}": random_string(10) for i in range(1, 51)}

    data = []

    for i in range(10000):
        data.append(long_dict)

    # Create a StringIO object to hold the CSV data
    csv_string_io = io.StringIO()

    # Create a CSV writer and write the header
    header = data[0].keys()
    csv_writer = csv.DictWriter(csv_string_io, fieldnames=header)
    csv_writer.writeheader()

    # Write the data rows to the StringIO object
    csv_writer.writerows(data)

    csv_string_io.seek(0)

    return csv_string_io


if __name__ == '__main__':
    # get public key from secret manager
    public_key = access_secret_version(project_id=PROJECT_ID, secret_id=PUBLIC_KEY_SECRET_ID, version_id=1)

    # Initialize the GnuPG instance
    gpg = gnupg.GPG()
    gpg.import_keys(key_data=public_key)
    # trusting imported key is important, or it will return an empty string as encrypted data
    gpg.trust_keys(fingerprints='71FEDB8B44D15B1AF199797A939B462CCE5D8DB8', trustlevel='TRUST_ULTIMATE')
    recipient = 'no-passwd@example.com'

    # generate a csv file in memory with some content
    in_memory_csv = generate_in_memory_csv()

    encrypted_ascii_data = gpg.encrypt(data=in_memory_csv.getvalue(), recipients=[recipient])

    if not encrypted_ascii_data:
        raise RuntimeError('cannot encrypt data, encrypted data is empty')

    now = datetime.now()
    timestamp_date = now.strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    bucket_name = f'{PROJECT_ID}-demo-gpg-encrypted'
    destination_blob_name = f"{timestamp_date}/gpg_demo_encrypted_{timestamp_str}.csv.gpg"

    upload_stringio_to_gcs(
        bucket_name=bucket_name,
        destination_blob_name=destination_blob_name,
        string_data=str(encrypted_ascii_data)
    )
