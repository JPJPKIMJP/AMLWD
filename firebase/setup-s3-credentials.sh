#!/bin/bash

echo "Setting up S3 credentials in Firebase Functions config..."

# Set S3 volume credentials
firebase functions:config:set \
  s3volume.endpoint="https://s3api-us-ks-2.runpod.io" \
  s3volume.bucket="82elxnhs55" \
  s3volume.access_key="user_2zH4PpHJhiBtUPAk4NUr6fhk3YG" \
  s3volume.secret_key="rps_188FHICZ3JLSLYHHLAPAGG6X9DWQ5JU940ZIWM081subkx"

echo "S3 credentials configured!"
echo ""
echo "To deploy the functions with new config, run:"
echo "  cd firebase"
echo "  firebase deploy --only functions"
echo ""
echo "RunPod will now fetch S3 credentials from Firebase automatically!"