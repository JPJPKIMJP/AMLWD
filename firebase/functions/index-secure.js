const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

// Your RunPod credentials (stored in Firebase config)
const RUNPOD_API_KEY = functions.config().runpod?.api_key;
const RUNPOD_ENDPOINT_ID = functions.config().runpod?.endpoint_id;

// OPTION 1: Callable Function (Requires Authentication)
exports.generateImageSecure = functions.https.onCall(async (data, context) => {
  // Check if user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError(
      'unauthenticated', 
      'You must be logged in to generate images'
    );
  }

  // Optional: Check if user is verified or has specific claims
  if (!context.auth.token.email_verified) {
    throw new functions.https.HttpsError(
      'permission-denied',
      'Email must be verified to use this service'
    );
  }

  // Optional: Rate limiting per user
  const userId = context.auth.uid;
  const userRef = admin.firestore().collection('users').doc(userId);
  const userDoc = await userRef.get();
  
  if (userDoc.exists) {
    const userData = userDoc.data();
    const today = new Date().toDateString();
    
    if (userData.lastRequestDate === today && userData.requestCount >= 10) {
      throw new functions.https.HttpsError(
        'resource-exhausted',
        'Daily limit of 10 images reached'
      );
    }
    
    // Update request count
    await userRef.update({
      lastRequestDate: today,
      requestCount: userData.lastRequestDate === today ? userData.requestCount + 1 : 1
    });
  } else {
    // First time user
    await userRef.set({
      lastRequestDate: new Date().toDateString(),
      requestCount: 1,
      createdAt: admin.firestore.FieldValue.serverTimestamp()
    });
  }

  try {
    const { prompt, width = 512, height = 512, steps = 20, guidance_scale = 7.5 } = data;

    if (!prompt) {
      throw new functions.https.HttpsError('invalid-argument', 'Prompt is required');
    }

    // Call RunPod API
    const response = await fetch(`https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/runsync`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RUNPOD_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: {
          prompt,
          width,
          height,
          num_inference_steps: steps,
          guidance_scale,
        }
      })
    });

    const result = await response.json();

    if (!response.ok) {
      throw new functions.https.HttpsError('internal', 'Failed to generate image');
    }

    // Log the request for monitoring
    await admin.firestore().collection('image_generations').add({
      userId: context.auth.uid,
      userEmail: context.auth.token.email,
      prompt,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      success: true
    });

    return {
      success: true,
      image: result.output.image_base64,
      seed: result.output.seed
    };

  } catch (error) {
    console.error('Error generating image:', error);
    throw new functions.https.HttpsError('internal', 'Failed to generate image');
  }
});

// OPTION 2: HTTP Function with API Key (For server-to-server)
exports.generateImageAPI = functions.https.onRequest(async (req, res) => {
  // Check for API key in header
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey) {
    return res.status(401).json({ error: 'API key required' });
  }

  // Verify API key against Firestore
  const apiKeyDoc = await admin.firestore()
    .collection('api_keys')
    .where('key', '==', apiKey)
    .where('active', '==', true)
    .limit(1)
    .get();

  if (apiKeyDoc.empty) {
    return res.status(401).json({ error: 'Invalid API key' });
  }

  // Process request (similar to above)
  // ... rest of the implementation
});

// OPTION 3: Internal-only function (Can only be called by other Firebase services)
exports.generateImageInternal = functions.https.onCall(async (data, context) => {
  // This can only be called from your Firebase project
  // Perfect for use with Firebase Hosting + Cloud Functions
  
  // Verify the request is coming from your app
  if (!context.auth && !context.rawRequest.headers['x-appengine-internal']) {
    throw new functions.https.HttpsError(
      'permission-denied',
      'Internal function only'
    );
  }

  // Process the request...
});