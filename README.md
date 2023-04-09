# cloud-run-gpg-decryptor

A gpg decryptor service runs on cloud run to decrypt files from GCS as they land via the event triggered to PubSub

## Pre defined vars

```
export EV_PROJECT_ID=[PROJECT_ID]
export EV_PRIVATE_KEY_SECRET_ID=[EV_PRIVATE_KEY_SECRET_ID]
export EV_GPG_KEY_FINGERPRINTS=[GPG_KEY_FINGERPRINTS]
export EV_GPG_RECIPIENT=[GPG_RECIPIENT]
export EV_DESTINATION_BUCKET_NAME=[DESTINATION_BUCKET_NAME]

export REGION=[REGION]
export AF_REPO_NAME=[AF_REPO_NAME]
export IMAGE_NAME=[IMAGE_NAME]
export COMMIT_SHA=$(git rev-parse --short=8 HEAD)
export SA=[SA]
```

## Configure GCS notification

```
gcloud storage buckets notifications create gs://${BUCKET_NAME} --topic=${TOPIC_NAME}
```

## The encryptor example

See [encryptor_example.py](encryptor_example.py)

## Deploy decryptor service

See [decryptor.py](decryptor.py) for the source code. 

### Deploy via cloudbuild
#### Create Artifact Registry repo
```
gcloud artifacts repositories create ${AF_REPO_NAME} --repository-format=docker --location=${REGION}
```
#### Build & Deploy
```
gcloud builds submit --config cloudbuild.yaml --substitutions _PROJECT_ID=${EV_PROJECT_ID},_PRIVATE_KEY_SECRET_ID=${EV_PRIVATE_KEY_SECRET_ID},_GPG_KEY_FINGERPRINTS=${EV_GPG_KEY_FINGERPRINTS},_GPG_RECIPIENT=${EV_GPG_RECIPIENT},_DESTINATION_BUCKET_NAME=${EV_DESTINATION_BUCKET_NAME},_REPO_NAME=${AF_REPO_NAME},_IMAGE_NAME=${IMAGE_NAME},_COMMIT_SHA=${COMMIT_SHA},_REGION=${REGION},_SA=${SA}
```