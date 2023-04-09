# cloud-run-gpg-decryptor

A gpg decryptor service runs on cloud run to decrypt files from GCS as they land via the event triggered to PubSub

## Pre defined vars

```
export BUCKET_NAME=<>
export TOPIC_NAME=<>
```

## Configure GCS notification

```
gcloud storage buckets notifications create gs://${BUCKET_NAME} --topic=${TOPIC_NAME}
```

## The encryptor example

See [encryptor_example.py](encryptor_example.py)

## The decryptor service

See [decryptor.py](decryptor.py)