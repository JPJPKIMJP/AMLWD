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

  // Rate limiting with transaction to prevent race conditions
  const userId = context.auth.uid;
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
          width: validatedInput.width,
          height: validatedInput.height,
          num_inference_steps: validatedInput.steps,
          guidance_scale: validatedInput.guidance_scale,
        }
      })
    });

    const result = await response.json();

    if (!response.ok || !result.output?.image_base64) {
      console.error('RunPod API error:', result);
      throw new functions.https.HttpsError('internal', 'Failed to generate image');
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
      image: result.output.image_base64,
      seed: result.output.seed,
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
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});