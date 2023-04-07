import os

from google.cloud import kms


def get_public_key_from_kms(project_id, location_id, key_ring_id, key_id, version_id):
    client = kms.KeyManagementServiceClient()
    key_version_name = client.crypto_key_version_path(project_id, location_id, key_ring_id, key_id, version_id)

    return client.get_public_key(request={'name': key_version_name})


def save_as_pem(file_name, key):
    with open(f'./{file_name}.pem', 'w+') as fp:
        fp.write(key.pem)


if __name__ == '__main__':
    PROJECT_ID = os.environ.get('PROJECT_ID')
    LOCATION_ID = 'europe-west2'
    KEY_RING_ID = 'gpg'
    KEY_ID = 'gpg-pair'
    VERSION_ID = "1"

    public_key = get_public_key_from_kms(
        project_id=PROJECT_ID,
        location_id=LOCATION_ID,
        key_ring_id=KEY_RING_ID,
        key_id=KEY_ID,
        version_id=VERSION_ID
    )

    save_as_pem(file_name='my_public_key', key=public_key)
