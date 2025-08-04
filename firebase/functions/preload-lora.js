// Add this to your index.js file

// Pre-load LoRA to RunPod S3 after upload
exports.preloadLoraToS3 = functions.https.onCall(async (data, context) => {
  // Check if user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'You must be logged in');
  }

  const { loraUrl, loraName } = data;
  
  if (!loraUrl || !loraName) {
    throw new functions.https.HttpsError('invalid-argument', 'LoRA URL and name are required');
  }

  try {
    const AWS = require('aws-sdk');
    const axios = require('axios');
    const path = require('path');
    
    // Ensure .safetensors extension
    const fileName = loraName.endsWith('.safetensors') ? loraName : `${loraName}.safetensors`;
    const s3Key = `ComfyUI/models/loras/${fileName}`;
    
    console.log(`Pre-loading LoRA: ${fileName} from ${loraUrl.substring(0, 50)}...`);
    
    // Configure S3 client for RunPod
    const s3 = new AWS.S3({
      endpoint: S3_ENDPOINT,
      accessKeyId: S3_ACCESS_KEY,
      secretAccessKey: S3_SECRET_KEY,
      region: 'US-KS-2',
      signatureVersion: 'v4',
      s3ForcePathStyle: true
    });
    
    // Check if already exists in S3
    try {
      await s3.headObject({
        Bucket: S3_BUCKET,
        Key: s3Key
      }).promise();
      
      console.log(`LoRA already exists in S3: ${s3Key}`);
      return {
        success: true,
        message: 'LoRA already pre-loaded',
        s3Key: s3Key,
        alreadyExists: true
      };
    } catch (e) {
      // File doesn't exist, proceed with upload
    }
    
    // Download from Firebase Storage
    console.log('Downloading from Firebase Storage...');
    const response = await axios({
      method: 'get',
      url: loraUrl,
      responseType: 'stream',
      maxContentLength: Infinity,
      maxBodyLength: Infinity
    });
    
    // Get file size from headers
    const fileSize = parseInt(response.headers['content-length'] || '0');
    console.log(`File size: ${(fileSize / 1024 / 1024).toFixed(1)}MB`);
    
    // Check if it's a FLUX LoRA
    if (fileSize < 200 * 1024 * 1024) {
      console.warn('File size suggests this might be an SD1.5 LoRA, not FLUX-compatible');
    }
    
    // Upload to S3
    console.log(`Uploading to S3: ${s3Key}`);
    const uploadResult = await s3.upload({
      Bucket: S3_BUCKET,
      Key: s3Key,
      Body: response.data,
      ContentType: 'application/octet-stream'
    }).promise();
    
    console.log(`Successfully pre-loaded to S3: ${uploadResult.Location}`);
    
    // Log the pre-load
    await admin.firestore().collection('lora_preloads').add({
      userId: context.auth.uid,
      userEmail: context.auth.token.email,
      loraName: fileName,
      s3Key: s3Key,
      fileSize: fileSize,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      firebaseUrl: loraUrl
    });
    
    return {
      success: true,
      message: 'LoRA pre-loaded successfully',
      s3Key: s3Key,
      fileSize: fileSize
    };
    
  } catch (error) {
    console.error('Pre-load error:', error);
    throw new functions.https.HttpsError('internal', `Failed to pre-load LoRA: ${error.message}`);
  }
});