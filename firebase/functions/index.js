const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

// Your RunPod credentials (stored in Firebase config)
const RUNPOD_API_KEY = functions.config().runpod?.api_key;
const RUNPOD_ENDPOINT_ID = functions.config().runpod?.endpoint_id;

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
  const { prompt, width = 512, height = 512, steps = 20, guidance_scale = 7.5 } = data;
  
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
  
  // Steps validation
  if (!ALLOWED_STEPS.includes(steps)) {
    throw new functions.https.HttpsError(
      'invalid-argument',
      `Steps must be one of: ${ALLOWED_STEPS.join(', ')}`
    );
  }
  
  // Guidance scale validation
  if (typeof guidance_scale !== 'number' || guidance_scale < MIN_GUIDANCE || guidance_scale > MAX_GUIDANCE) {
    throw new functions.https.HttpsError(
      'invalid-argument',
      `Guidance scale must be between ${MIN_GUIDANCE} and ${MAX_GUIDANCE}`
    );
  }
  
  return { prompt, width, height, steps, guidance_scale };
}

// Secure callable function with improved rate limiting
exports.generateImageSecure = functions.https.onCall(async (data, context) => {
  // Check if user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError(
      'unauthenticated', 
      'You must be logged in to generate images'
    );
  }

  // Check if user is verified
  if (!context.auth.token.email_verified) {
    throw new functions.https.HttpsError(
      'permission-denied',
      'Email must be verified to use this service'
    );
  }

  // Validate input
  const validatedInput = validateInput(data);

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
    
    // Call RunPod API
    const response = await fetch(`https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/runsync`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RUNPOD_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: {
          prompt: validatedInput.prompt,
          negative_prompt: "",
          width: validatedInput.width,
          height: validatedInput.height,
          num_inference_steps: validatedInput.steps,
          guidance_scale: validatedInput.guidance_scale,
          seed: -1,
          scheduler: "K_EULER"  // SDXL scheduler
        }
      })
    });

    const result = await response.json();
    console.log('RunPod response:', JSON.stringify(result));

    if (!response.ok) {
      console.error('RunPod API error:', result);
      throw new functions.https.HttpsError('internal', 'Failed to generate image');
    }

    // Handle RunPod response - check if we need to fetch the result
    let imageBase64;
    
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
    
    // Now check for the image in various formats
    if (result.output?.image_url) {
      // SDXL returns image_url with base64 data
      imageBase64 = result.output.image_url;
      // If it starts with data:image, extract just the base64 part
      if (imageBase64.startsWith('data:image')) {
        imageBase64 = imageBase64.split(',')[1];
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
      
      // Check if the result has any keys that might contain the image
      const possibleImageKeys = Object.keys(result).filter(key => 
        key.toLowerCase().includes('image') || 
        key.toLowerCase().includes('output') || 
        key.toLowerCase().includes('result') ||
        key.toLowerCase().includes('url')
      );
      
      if (possibleImageKeys.length > 0) {
        console.log('Found possible image keys:', possibleImageKeys);
      }
      
      throw new functions.https.HttpsError(
        'internal', 
        'Image generation completed but output format not recognized. Check logs for details.'
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
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      processingTime: processingTime,
      success: true
    });

    return {
      success: true,
      image: imageBase64,
      seed: result.output?.seed || -1,
      processingTime: processingTime
    };

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
    version: '2.0.0-sdxl-admin',  // Updated: SDXL support + admin bypass
    deployedAt: '2025-07-23T08:05:00Z',
    features: [
      'SDXL model support',
      'Admin rate limit bypass',
      'image_url output handling',
      'Enhanced error logging'
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
    await admin.firestore().collection('users').doc(userId).update({
      requestCount: 0,
      lastRequestDate: new Date('2024-01-01').toDateString()
    });
    
    return { success: true, message: 'Rate limit reset successfully' };
  } catch (error) {
    console.error('Reset error:', error);
    throw new functions.https.HttpsError('internal', 'Failed to reset rate limit');
  }
});

// Test RunPod endpoint - callable function for testing
exports.testRunPod = functions.https.onCall(async (data, context) => {
  // Check if user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'You must be logged in');
  }

  if (!RUNPOD_API_KEY || !RUNPOD_ENDPOINT_ID) {
    throw new functions.https.HttpsError('failed-precondition', 'RunPod not configured');
  }

  try {
    // Try a minimal test with the endpoint
    const response = await fetch(`https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/runsync`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RUNPOD_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: {
          prompt: "test image, simple shape",
          width: 512,
          height: 512,
          num_inference_steps: 1,  // Minimal steps for testing
          guidance_scale: 7.5
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