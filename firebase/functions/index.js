const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

// Your RunPod credentials (stored in Firebase config)
const RUNPOD_API_KEY = functions.config().runpod?.api_key;
const RUNPOD_ENDPOINT_ID = functions.config().runpod?.endpoint_id;

// S3 Volume credentials for RunPod (stored in Firebase config)
const S3_ENDPOINT = functions.config().s3volume?.endpoint || 'https://s3api-us-ks-2.runpod.io';
const S3_BUCKET = functions.config().s3volume?.bucket || '82elxnhs55';
const S3_ACCESS_KEY = functions.config().s3volume?.access_key;
const S3_SECRET_KEY = functions.config().s3volume?.secret_key;

// Constants for validation
const MAX_PROMPT_LENGTH = 1000;
const MIN_PROMPT_LENGTH = 3;
const ALLOWED_DIMENSIONS = [256, 512, 768, 1024];
const ALLOWED_STEPS = [10, 15, 20, 25, 30, 40, 50];
const MIN_GUIDANCE = 1;
const MAX_GUIDANCE = 20;
const DAILY_LIMIT = 10;

// Inappropriate content keywords (basic filter)
const BLOCKED_KEYWORDS = [
  // Add inappropriate keywords here
  // This is a basic filter - consider using AI-based content moderation
];

// Input validation function
function validateInput(data) {
  const { 
    prompt, 
    negative_prompt = "",
    width = 1024, 
    height = 1024, 
    steps = 25, 
    guidance_scale = 7.5,
    num_images = 1,
    seed = -1,
    sampler_name = "DPM++ 2M Karras",
    scheduler = "normal",
    refiner_inference_steps = 0,
    high_noise_frac = 0.8
  } = data;
  
  // Prompt validation
  if (!prompt || typeof prompt !== 'string') {
    throw new functions.https.HttpsError('invalid-argument', 'Prompt is required and must be a string');
  }
  
  if (prompt.length < MIN_PROMPT_LENGTH || prompt.length > MAX_PROMPT_LENGTH) {
    throw new functions.https.HttpsError(
      'invalid-argument', 
      `Prompt must be between ${MIN_PROMPT_LENGTH} and ${MAX_PROMPT_LENGTH} characters`
    );
  }
  
  // Basic content filtering
  const promptLower = prompt.toLowerCase();
  for (const keyword of BLOCKED_KEYWORDS) {
    if (promptLower.includes(keyword)) {
      throw new functions.https.HttpsError(
        'invalid-argument',
        'Prompt contains inappropriate content'
      );
    }
  }
  
  // Dimension validation
  if (!ALLOWED_DIMENSIONS.includes(width) || !ALLOWED_DIMENSIONS.includes(height)) {
    throw new functions.https.HttpsError(
      'invalid-argument',
      `Dimensions must be one of: ${ALLOWED_DIMENSIONS.join(', ')}`
    );
  }
  
  // Steps validation (relaxed for SDXL)
  if (typeof steps !== 'number' || steps < 1 || steps > 100) {
    throw new functions.https.HttpsError(
      'invalid-argument',
      'Steps must be between 1 and 100'
    );
  }
  
  // Guidance scale validation
  if (typeof guidance_scale !== 'number' || guidance_scale < MIN_GUIDANCE || guidance_scale > MAX_GUIDANCE) {
    throw new functions.https.HttpsError(
      'invalid-argument',
      `Guidance scale must be between ${MIN_GUIDANCE} and ${MAX_GUIDANCE}`
    );
  }
  
  // Number of images validation
  if (typeof num_images !== 'number' || num_images < 1 || num_images > 4) {
    throw new functions.https.HttpsError(
      'invalid-argument',
      'Number of images must be between 1 and 4'
    );
  }
  
  // For template endpoints, split large batches into multiple requests
  if (num_images > 2 && (width > 512 || height > 512)) {
    console.warn(`Large batch requested: ${num_images} images at ${width}x${height} - will be split into multiple requests`);
  }
  
  return { 
    prompt, 
    negative_prompt,
    width, 
    height, 
    steps, 
    guidance_scale,
    num_images,
    seed,
    sampler_name,
    scheduler,
    refiner_inference_steps,
    high_noise_frac
  };
}

// Secure callable function with improved rate limiting
exports.generateImageSecure = functions
  .runWith({
    timeoutSeconds: 540,  // 9 minutes (max allowed)
    memory: '2GB'         // Increase memory for better performance
  })
  .https.onCall(async (data, context) => {
  // Check if user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError(
      'unauthenticated', 
      'You must be logged in to generate images'
    );
  }

  // Email verification removed - too much friction for users
  // Just being authenticated is enough

  // Validate input
  const validatedInput = validateInput(data);
  
  // Extract image if provided (for img2img)
  const inputImageBase64 = data.image;

  // Check if user is admin
  const userId = context.auth.uid;
  const userEmail = context.auth.token.email;
  let isAdmin = false;
  
  console.log(`Checking admin status for user: ${userEmail} (${userId})`);
  
  // Check admin status
  try {
    const adminDoc = await admin.firestore().collection('admins').doc(userId).get();
    console.log(`Admin doc exists: ${adminDoc.exists}, data:`, adminDoc.exists ? adminDoc.data() : 'N/A');
    isAdmin = adminDoc.exists && adminDoc.data()?.isAdmin === true;
    
    if (isAdmin) {
      console.log(`Admin user ${userEmail} bypassing rate limit`);
    } else {
      console.log(`User ${userEmail} is not admin, applying rate limit`);
    }
  } catch (error) {
    console.error('Error checking admin status:', error);
  }
  
  // Skip rate limiting for admin users
  if (!isAdmin) {
    // Rate limiting with transaction to prevent race conditions
    const userRef = admin.firestore().collection('users').doc(userId);
    
    try {
      // Use transaction for atomic rate limit check and update
      const canProceed = await admin.firestore().runTransaction(async (transaction) => {
        const userDoc = await transaction.get(userRef);
        const now = new Date();
        const today = now.toDateString();
        
        if (userDoc.exists) {
          const userData = userDoc.data();
          
          // Check daily limit
          if (userData.lastRequestDate === today && userData.requestCount >= DAILY_LIMIT) {
            throw new functions.https.HttpsError(
              'resource-exhausted',
              `Daily limit of ${DAILY_LIMIT} images reached. Resets at midnight.`
            );
          }
          
          // Update count atomically
          transaction.update(userRef, {
            lastRequestDate: today,
            requestCount: userData.lastRequestDate === today ? userData.requestCount + 1 : 1,
            lastRequestTime: admin.firestore.FieldValue.serverTimestamp()
          });
        } else {
          // Create new user record
          transaction.set(userRef, {
            lastRequestDate: today,
            requestCount: 1,
            createdAt: admin.firestore.FieldValue.serverTimestamp(),
            lastRequestTime: admin.firestore.FieldValue.serverTimestamp(),
            email: context.auth.token.email,
            userId: userId
          });
        }
        
        return true;
      });
      
      if (!canProceed) {
        throw new functions.https.HttpsError('internal', 'Rate limit check failed');
      }
      
    } catch (error) {
      // Re-throw if it's already an HttpsError
      if (error.code && error.code.startsWith('functions/')) {
        throw error;
      }
      console.error('Transaction error:', error);
      throw new functions.https.HttpsError('internal', 'Failed to process rate limit');
    }
  }

  // Check if RunPod credentials are configured
  if (!RUNPOD_API_KEY || !RUNPOD_ENDPOINT_ID) {
    console.error('RunPod credentials not configured');
    throw new functions.https.HttpsError(
      'failed-precondition',
      'Service not properly configured. Please contact support.'
    );
  }

  // Generate image
  try {
    const startTime = Date.now();
    
    // Build request payload
    const requestPayload = {
      prompt: validatedInput.prompt,
      width: validatedInput.width,
      height: validatedInput.height,
      // Add image for img2img if provided
      ...(inputImageBase64 && { image: inputImageBase64 }),
      // Add LoRA parameters if provided
      ...(data.lora_name && data.lora_name !== 'none' && { 
        lora_name: data.lora_name,
        lora_strength: data.lora_strength || 0.8,
        // If custom LoRA URL is provided, include it
        ...(data.lora_url && { lora_url: data.lora_url })
      }),
      // FLUX doesn't use these traditional parameters
      // num_inference_steps: validatedInput.steps,
      // guidance_scale: validatedInput.guidance_scale,
      // negative_prompt is not used in FLUX
      // ...(validatedInput.seed !== -1 && { seed: validatedInput.seed }),
      // ...(validatedInput.num_images > 1 && { num_images: validatedInput.num_images })
    };
    
    // Log if custom LoRA is being used
    if (data.lora_url) {
      console.log('Using custom LoRA from URL:', data.lora_url);
    }
    
    console.log('Sending to RunPod:', JSON.stringify(requestPayload));
    
    // Call RunPod API with minimal SDXL parameters
    // Use AbortController for custom timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout
    
    const response = await fetch(`https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/runsync`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RUNPOD_API_KEY}`,
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
      body: JSON.stringify({
        input: requestPayload
      })
    }).finally(() => {
      clearTimeout(timeoutId);
    });

    let result = await response.json();
    console.log('RunPod initial response:', JSON.stringify(result));

    if (!response.ok) {
      console.error('RunPod API error:', result);
      throw new functions.https.HttpsError('internal', 'Failed to generate image');
    }


    // Handle RunPod response - check if we need to fetch the result
    let imageBase64;
    
    // Handle IN_PROGRESS or IN_QUEUE status (FLUX takes too long for sync endpoint)
    if ((result.status === 'IN_PROGRESS' || result.status === 'IN_QUEUE') && result.id) {
      console.log(`Job status: ${result.status}, polling for completion...`);
      
      // Poll for up to 8 minutes (leaving buffer for 9-minute function timeout)
      const maxAttempts = 96; // 96 * 5 seconds = 8 minutes
      let attempts = 0;
      
      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
        
        const statusResponse = await fetch(`https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/status/${result.id}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${RUNPOD_API_KEY}`,
          }
        });
        
        if (statusResponse.ok) {
          const statusResult = await statusResponse.json();
          console.log(`Attempt ${attempts + 1}: Status = ${statusResult.status}`);
          
          if (statusResult.status === 'COMPLETED') {
            result = statusResult;
            break;
          } else if (statusResult.status === 'FAILED') {
            console.error('Job failed:', statusResult);
            throw new functions.https.HttpsError('internal', `RunPod job failed: ${statusResult.error || 'Unknown error'}`);
          }
        }
        
        attempts++;
      }
      
      if (attempts >= maxAttempts) {
        throw new functions.https.HttpsError('deadline-exceeded', 'Image generation timed out after 8 minutes');
      }
    }
    
    // If status is COMPLETED but no output, try the async pattern
    if (result.status === 'COMPLETED' && result.id && !result.output) {
      console.log('No output in sync response, trying async pattern...');
      
      // First try the status endpoint
      const statusResponse = await fetch(`https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/status/${result.id}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${RUNPOD_API_KEY}`,
        }
      });
      
      if (statusResponse.ok) {
        const statusResult = await statusResponse.json();
        console.log('Status response:', JSON.stringify(statusResult));
        result.output = statusResult.output;
      }
      
      // If still no output, try using run instead of runsync
      if (!result.output) {
        console.log('Status endpoint did not return output. The endpoint might need async pattern.');
        // For SDXL, the output might be in a different field or require different handling
        // Check if there's any other data in the result
        console.log('Full result object keys:', Object.keys(result));
        
        // Some SDXL endpoints return the image URL instead of base64
        if (result.output_url) {
          console.log('Found output_url, fetching image...');
          const imageResponse = await fetch(result.output_url);
          if (imageResponse.ok) {
            const blob = await imageResponse.blob();
            const buffer = await blob.arrayBuffer();
            imageBase64 = Buffer.from(buffer).toString('base64');
            result.output = { image_base64: imageBase64 };
          }
        }
      }
    }
    
    // Check if we got URLs from R2 (new format)
    if (result.output?.images && Array.isArray(result.output.images) && 
        result.output.images.length > 0 && 
        typeof result.output.images[0] === 'string' && 
        result.output.images[0].startsWith('http')) {
      
      console.log('Received R2 URLs:', result.output.images);
      
      // Fetch images from R2 URLs and convert to base64 for immediate display
      const imagePromises = result.output.images.map(async (url) => {
        try {
          const response = await fetch(url);
          if (!response.ok) throw new Error('Failed to fetch image');
          
          const buffer = await response.arrayBuffer();
          return Buffer.from(buffer).toString('base64');
        } catch (error) {
          console.error('Error fetching image from R2:', error);
          return null;
        }
      });
      
      const images = await Promise.all(imagePromises);
      const validImages = images.filter(img => img !== null);
      
      if (validImages.length === 0) {
        throw new functions.https.HttpsError('internal', 'Failed to fetch generated images from storage');
      }
      
      // Return multiple images
      if (validImages.length > 1) {
        return {
          success: true,
          images: validImages,
          urls: result.output.images, // Also return URLs for direct access
          seed: result.output?.seed || -1,
          processingTime: Date.now() - startTime
        };
      } else {
        return {
          success: true,
          image: validImages[0],
          url: result.output.images[0],
          seed: result.output?.seed || -1,
          processingTime: Date.now() - startTime
        };
      }
      
    } else if (result.output?.image_url) {
      // FLUX handler returns image_url when using R2
      if (result.output.image_url.startsWith('http')) {
        console.log('Fetching image from URL:', result.output.image_url);
        try {
          const imageResponse = await fetch(result.output.image_url);
          if (imageResponse.ok) {
            const blob = await imageResponse.blob();
            const buffer = await blob.arrayBuffer();
            imageBase64 = Buffer.from(buffer).toString('base64');
          } else {
            throw new Error('Failed to fetch image from URL');
          }
        } catch (fetchError) {
          console.error('Error fetching image:', fetchError);
          throw new functions.https.HttpsError('internal', 'Failed to fetch generated image from URL');
        }
      } else {
        // It's base64 data
        imageBase64 = result.output.image_url;
        if (imageBase64.startsWith('data:image')) {
          imageBase64 = imageBase64.split(',')[1];
        }
      }
    } else if (result.output?.images && Array.isArray(result.output.images) && result.output.images[0]) {
      // SDXL might return array of images
      imageBase64 = result.output.images[0];
      if (imageBase64.startsWith('data:image')) {
        imageBase64 = imageBase64.split(',')[1];
      }
    } else if (result.output?.image_base64) {
      imageBase64 = result.output.image_base64;
    } else if (result.output && typeof result.output === 'string') {
      imageBase64 = result.output;
    } else if (Array.isArray(result.output) && result.output[0]) {
      imageBase64 = result.output[0];
    } else if (result.output?.image) {
      imageBase64 = result.output.image;
    } else {
      // Log everything we have for debugging
      console.error('Unexpected output format. Full result:', JSON.stringify(result, null, 2));
      console.error('Result.output value:', result.output);
      console.error('Result.output type:', typeof result.output);
      console.error('Result.status:', result.status);
      console.error('Result keys:', Object.keys(result));
      
      // Special handling for RunPod errors
      if (result.error) {
        console.error('RunPod error:', result.error);
        if (result.error.includes('Failed to return job results') && result.error.includes('400')) {
          throw new functions.https.HttpsError(
            'internal', 
            'RunPod error: Image too large for sync endpoint. Try smaller dimensions or fewer steps.'
          );
        }
        throw new functions.https.HttpsError('internal', `RunPod error: ${result.error}`);
      }
      
      // Check if FLUX handler returned an error
      if (result.output?.status === 'error' && result.output?.error) {
        console.error('FLUX handler error:', result.output.error);
        throw new functions.https.HttpsError('internal', `FLUX generation failed: ${result.output.error}`);
      }
      
      // Check if output is null/undefined but status is COMPLETED
      if (result.status === 'COMPLETED' && (result.output === null || result.output === undefined)) {
        console.error('RunPod returned COMPLETED but output is null/undefined. This indicates the response was too large.');
        throw new functions.https.HttpsError(
          'internal', 
          'Image generation failed: Output too large. Try reducing image size to 768x768 or fewer steps.'
        );
      }
      
      throw new functions.https.HttpsError(
        'internal', 
        'Image generation failed. Try smaller dimensions (768x768) or contact support.'
      );
    }

    const processingTime = Date.now() - startTime;

    // Log successful generation
    await admin.firestore().collection('image_generations').add({
      userId: context.auth.uid,
      userEmail: context.auth.token.email,
      prompt: validatedInput.prompt,
      width: validatedInput.width,
      height: validatedInput.height,
      steps: validatedInput.steps,
      guidanceScale: validatedInput.guidance_scale,
      loraName: data.lora_name || null,
      loraStrength: data.lora_strength || null,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      processingTime: processingTime,
      success: true
    });

    // Handle multiple images if num_images > 1
    if (validatedInput.num_images > 1 && result.output?.images) {
      return {
        success: true,
        images: result.output.images.map(img => {
          // Extract base64 if it's a data URI
          if (img.startsWith('data:image')) {
            return img.split(',')[1];
          }
          return img;
        }),
        seed: result.output?.seed || -1,
        processingTime: processingTime
      };
    } else {
      return {
        success: true,
        image: imageBase64,
        seed: result.output?.seed || -1,
        processingTime: processingTime
      };
    }

  } catch (error) {
    // Log failed generation
    await admin.firestore().collection('image_generations').add({
      userId: context.auth.uid,
      userEmail: context.auth.token.email,
      prompt: validatedInput.prompt,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      success: false,
      error: error.message
    }).catch(console.error); // Don't fail if logging fails

    console.error('Error generating image:', error);
    throw new functions.https.HttpsError('internal', 'Failed to generate image');
  }
});

// Save image to Firebase Storage
exports.saveImageToStorage = functions.https.onCall(async (data, context) => {
  // Check if user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'You must be logged in');
  }

  const { imageBase64, prompt, metadata = {} } = data;
  
  if (!imageBase64 || !prompt) {
    throw new functions.https.HttpsError('invalid-argument', 'Image and prompt are required');
  }

  try {
    const userId = context.auth.uid;
    const timestamp = Date.now();
    const fileName = `images/${userId}/${timestamp}_${Math.random().toString(36).substring(7)}.png`;
    
    // Convert base64 to buffer
    const imageBuffer = Buffer.from(imageBase64, 'base64');
    
    // Get a reference to the storage bucket
    const bucket = admin.storage().bucket();
    
    // Check if bucket exists
    try {
      const [exists] = await bucket.exists();
      if (!exists) {
        console.error('Storage bucket does not exist. Firebase Storage needs to be enabled.');
        throw new functions.https.HttpsError(
          'failed-precondition', 
          'Firebase Storage is not enabled. Please enable it in the Firebase Console.'
        );
      }
    } catch (checkError) {
      console.error('Error checking bucket:', checkError);
      // Continue anyway as the bucket might exist but we can't check
    }
    
    const file = bucket.file(fileName);
    
    // Upload the image
    await file.save(imageBuffer, {
      metadata: {
        contentType: 'image/png',
        metadata: {
          userId: userId,
          userEmail: context.auth.token.email,
          prompt: prompt,
          timestamp: timestamp.toString(),
          ...metadata
        }
      }
    });
    
    // Make the file publicly readable
    await file.makePublic();
    
    // Get the public URL
    const publicUrl = `https://storage.googleapis.com/${bucket.name}/${fileName}`;
    
    // Save metadata to Firestore
    const docRef = await admin.firestore().collection('user_images').add({
      userId: userId,
      userEmail: context.auth.token.email,
      prompt: prompt,
      imageUrl: publicUrl,
      fileName: fileName,
      size: imageBuffer.length,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      metadata: metadata
    });
    
    return {
      success: true,
      imageUrl: publicUrl,
      docId: docRef.id,
      fileName: fileName
    };
    
  } catch (error) {
    console.error('Error saving image:', error);
    throw new functions.https.HttpsError('internal', 'Failed to save image');
  }
});

// Get user's image history
exports.getUserImages = functions.https.onCall(async (data, context) => {
  // Check if user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'You must be logged in');
  }

  try {
    const userId = context.auth.uid;
    const { limit = 20, startAfter = null } = data;
    
    let query = admin.firestore()
      .collection('user_images')
      .where('userId', '==', userId)
      .orderBy('timestamp', 'desc')
      .limit(limit);
    
    if (startAfter) {
      const startDoc = await admin.firestore().collection('user_images').doc(startAfter).get();
      if (startDoc.exists) {
        query = query.startAfter(startDoc);
      }
    }
    
    const snapshot = await query.get();
    const images = [];
    
    snapshot.forEach(doc => {
      images.push({
        id: doc.id,
        ...doc.data(),
        timestamp: doc.data().timestamp?.toDate?.() || new Date()
      });
    });
    
    return {
      success: true,
      images: images,
      hasMore: images.length === limit
    };
    
  } catch (error) {
    console.error('Error fetching images:', error);
    throw new functions.https.HttpsError('internal', 'Failed to fetch images');
  }
});

// Health check endpoint
exports.healthCheck = functions.https.onRequest((req, res) => {
  // Set CORS headers
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET, POST');
  res.set('Access-Control-Allow-Headers', 'Content-Type');
  
  // Handle preflight OPTIONS request
  if (req.method === 'OPTIONS') {
    res.status(204).send('');
    return;
  }
  
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '2.2.1',  // Fixed: Don't send URLs for pre-loaded LoRAs
    deployedAt: new Date().toISOString(),
    features: [
      'FLUX model support',
      'Admin rate limit bypass',
      'Firebase Storage integration',
      'RunPod S3 volume integration',
      'Automatic LoRA pre-loading',
      'Pre-installed LoRAs support',
      'No download delays for pre-loaded LoRAs'
    ]
  });
});

// Reset rate limit for admin - temporary function
exports.resetRateLimit = functions.https.onCall(async (data, context) => {
  // Check if user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'You must be logged in');
  }
  
  // Only allow for specific admin email
  if (context.auth.token.email !== 'goooodjp@gmail.com') {
    throw new functions.https.HttpsError('permission-denied', 'Not authorized');
  }
  
  try {
    const userId = context.auth.uid;
    
    // Reset rate limit
    await admin.firestore().collection('users').doc(userId).update({
      requestCount: 0,
      lastRequestDate: new Date('2024-01-01').toDateString()
    });
    
    // Also make sure admin status is set
    await admin.firestore().collection('admins').doc(userId).set({
      isAdmin: true,
      email: context.auth.token.email,
      addedAt: admin.firestore.FieldValue.serverTimestamp()
    });
    
    return { success: true, message: 'Rate limit reset and admin status confirmed' };
  } catch (error) {
    console.error('Reset error:', error);
    throw new functions.https.HttpsError('internal', 'Failed to reset rate limit');
  }
});

// Get S3 credentials for RunPod - secure endpoint
exports.getS3Credentials = functions.https.onRequest(async (req, res) => {
  // Set CORS headers
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    res.status(204).send('');
    return;
  }
  
  // Verify the request is from RunPod by checking a shared secret
  const authHeader = req.headers.authorization;
  const runpodSecret = functions.config().runpod?.secret || RUNPOD_API_KEY;
  
  if (!authHeader || authHeader !== `Bearer ${runpodSecret}`) {
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }
  
  // Return S3 credentials
  res.status(200).json({
    S3_ENDPOINT: S3_ENDPOINT,
    S3_BUCKET: S3_BUCKET,
    S3_ACCESS_KEY: S3_ACCESS_KEY,
    S3_SECRET_KEY: S3_SECRET_KEY
  });
});

// Test RunPod endpoint - callable function for testing
exports.testRunPod = functions
  .runWith({
    timeoutSeconds: 540,
    memory: '2GB'
  })
  .https.onCall(async (data, context) => {
  // Check if user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'You must be logged in');
  }

  if (!RUNPOD_API_KEY || !RUNPOD_ENDPOINT_ID) {
    throw new functions.https.HttpsError('failed-precondition', 'RunPod not configured');
  }

  try {
    // Try a minimal test with smaller image
    const response = await fetch(`https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/runsync`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RUNPOD_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: {
          prompt: "simple red circle on white background",
          width: 256,  // Very small to test
          height: 256,
          num_inference_steps: 10,
          guidance_scale: 7.5,
          seed: 42
        }
      })
    });

    const result = await response.json();
    
    // Return full response for debugging
    return {
      success: response.ok,
      status: response.status,
      result: result,
      endpoint_id: RUNPOD_ENDPOINT_ID.substring(0, 6) + '...',  // Partial ID for security
      headers: Object.fromEntries(response.headers.entries())
    };
  } catch (error) {
    console.error('Test error:', error);
    throw new functions.https.HttpsError('internal', error.message);
  }
});

// Pre-load LoRA to RunPod S3 after upload
exports.preloadLoraToS3 = functions
  .runWith({
    timeoutSeconds: 300,  // 5 minutes for large files
    memory: '1GB'
  })
  .https.onCall(async (data, context) => {
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