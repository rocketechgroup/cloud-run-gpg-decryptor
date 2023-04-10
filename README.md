# cloud-run-gpg-decryptor

A gpg decryptor service runs on cloud run to decrypt files from GCS as they land via the event triggered to PubSub

## GPG Need to know

### How to generate and Export keys

This solution is a serverless solution and keys need to be exported from GPG keystore and saved to Secret Manager.
See the comprehensive guide from [johnfedoruk](https://gist.github.com/johnfedoruk/7f156d844af54cc91324dff4f54b11ce) on
how to generate and export keys from GPG

### The recipient

GPG works based on the association of a key to a recipient, which is typically an email address used when generating the key. 

This can be referenced when encrypting and decrypting.

### Trusting the imported key

The library we are using in this solution is called `python-gnupg`. This is probably the most maintained one on Python.

In this solution, we are importing the private key from Secret Manager on the fly, but in order to use it correctly, we
must trust the imported key using a given fingerprint.

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