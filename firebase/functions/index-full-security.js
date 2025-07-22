const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

// Your RunPod credentials (stored in Firebase config)
const RUNPOD_API_KEY = functions.config().runpod?.api_key;
const RUNPOD_ENDPOINT_ID = functions.config().runpod?.endpoint_id;

// Webhook URL for alerts (store in Firebase config)
const ALERT_WEBHOOK_URL = functions.config().alerts?.webhook_url;

// Cost thresholds
const COST_PER_IMAGE = 0.003; // Estimated cost per image in USD
const DAILY_COST_ALERT_THRESHOLD = 10; // Alert if daily cost exceeds $10
const MONTHLY_COST_ALERT_THRESHOLD = 100; // Alert if monthly cost exceeds $100

// Constants for validation
const MAX_PROMPT_LENGTH = 1000;
const MIN_PROMPT_LENGTH = 3;
const ALLOWED_DIMENSIONS = [256, 512, 768, 1024];
const ALLOWED_STEPS = [10, 15, 20, 25, 30, 40, 50];
const MIN_GUIDANCE = 1;
const MAX_GUIDANCE = 20;
const DAILY_LIMIT = 10;
const HOURLY_IP_LIMIT = 20;
const SUSPICIOUS_ACTIVITY_THRESHOLD = 5; // Failed attempts before alert

// Content moderation keywords (expandable)
const BLOCKED_KEYWORDS = [
  'illegal', 'violent', 'explicit',
  // Add more as needed
];

// Helper function to get client IP
function getClientIp(rawRequest) {
  const forwarded = rawRequest.headers['x-forwarded-for'];
  const ip = forwarded ? forwarded.split(',')[0] : rawRequest.connection.remoteAddress;
  return ip || 'unknown';
}

// Send webhook alert
async function sendAlert(title, message, severity = 'warning') {
  if (!ALERT_WEBHOOK_URL) return;
  
  try {
    await fetch(ALERT_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        message,
        severity,
        timestamp: new Date().toISOString(),
        project: 'amlwd-image-gen'
      })
    });
  } catch (error) {
    console.error('Failed to send alert:', error);
  }
}

// Check if user is blocked
async function isUserBlocked(userId) {
  const blockedRef = admin.firestore().collection('blocked_users').doc(userId);
  const blockedDoc = await blockedRef.get();
  
  if (blockedDoc.exists) {
    const data = blockedDoc.data();
    if (data.permanentBan) {
      return { blocked: true, reason: data.reason || 'Account suspended' };
    }
    
    // Check temporary suspension
    if (data.suspendedUntil && data.suspendedUntil.toDate() > new Date()) {
      return { 
        blocked: true, 
        reason: `Account suspended until ${data.suspendedUntil.toDate().toLocaleString()}`
      };
    }
  }
  
  return { blocked: false };
}

// Enhanced content moderation using perspective API (Google)
async function moderateContent(text) {
  // Basic keyword filter
  const textLower = text.toLowerCase();
  for (const keyword of BLOCKED_KEYWORDS) {
    if (textLower.includes(keyword)) {
      return { 
        safe: false, 
        reason: 'Contains prohibited content',
        flaggedKeyword: keyword 
      };
    }
  }
  
  // If Google Cloud Natural Language API is enabled, use it for better moderation
  try {
    // This is a placeholder - you'd need to set up Google Cloud Natural Language API
    // const language = require('@google-cloud/language');
    // const client = new language.LanguageServiceClient();
    // const document = { content: text, type: 'PLAIN_TEXT' };
    // const [result] = await client.analyzeSentiment({ document });
    
    // For now, return safe
    return { safe: true };
  } catch (error) {
    console.error('Content moderation error:', error);
    return { safe: true }; // Fail open for now
  }
}

// Track IP-based rate limiting
async function checkIpRateLimit(ip, userId) {
  const now = new Date();
  const hourAgo = new Date(now.getTime() - 60 * 60 * 1000);
  
  const ipRef = admin.firestore().collection('ip_rate_limits').doc(ip);
  
  return await admin.firestore().runTransaction(async (transaction) => {
    const ipDoc = await transaction.get(ipRef);
    
    if (ipDoc.exists) {
      const data = ipDoc.data();
      const recentRequests = (data.requests || []).filter(r => r.timestamp.toDate() > hourAgo);
      
      if (recentRequests.length >= HOURLY_IP_LIMIT) {
        // Log suspicious activity
        await sendAlert(
          'Rate Limit Exceeded',
          `IP ${ip} exceeded hourly limit. User: ${userId}`,
          'warning'
        );
        
        return { allowed: false, reason: 'Too many requests from this IP address' };
      }
      
      // Add new request
      recentRequests.push({
        userId,
        timestamp: admin.firestore.FieldValue.serverTimestamp()
      });
      
      transaction.update(ipRef, { requests: recentRequests });
    } else {
      // Create new IP record
      transaction.set(ipRef, {
        requests: [{
          userId,
          timestamp: admin.firestore.FieldValue.serverTimestamp()
        }],
        firstSeen: admin.firestore.FieldValue.serverTimestamp()
      });
    }
    
    return { allowed: true };
  });
}

// Monitor costs and send alerts
async function monitorCosts() {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  
  // Get today's generations
  const todayQuery = await admin.firestore()
    .collection('image_generations')
    .where('timestamp', '>=', todayStart)
    .where('success', '==', true)
    .get();
  
  const dailyCost = todayQuery.size * COST_PER_IMAGE;
  
  if (dailyCost > DAILY_COST_ALERT_THRESHOLD) {
    await sendAlert(
      'Daily Cost Alert',
      `Daily cost has reached $${dailyCost.toFixed(2)} (${todayQuery.size} images)`,
      'warning'
    );
  }
  
  // Get this month's generations
  const monthQuery = await admin.firestore()
    .collection('image_generations')
    .where('timestamp', '>=', monthStart)
    .where('success', '==', true)
    .get();
  
  const monthlyCost = monthQuery.size * COST_PER_IMAGE;
  
  if (monthlyCost > MONTHLY_COST_ALERT_THRESHOLD) {
    await sendAlert(
      'Monthly Cost Alert',
      `Monthly cost has reached $${monthlyCost.toFixed(2)} (${monthQuery.size} images)`,
      'critical'
    );
  }
  
  return { dailyCost, monthlyCost, dailyImages: todayQuery.size, monthlyImages: monthQuery.size };
}

// Enhanced input validation
function validateInput(data) {
  const { prompt, width = 512, height = 512, steps = 20, guidance_scale = 7.5 } = data;
  
  // Prompt validation
  if (!prompt || typeof prompt !== 'string') {
    throw new functions.https.HttpsError('invalid-argument', 'Prompt is required and must be a string');
  }
  
  const trimmedPrompt = prompt.trim();
  
  if (trimmedPrompt.length < MIN_PROMPT_LENGTH || trimmedPrompt.length > MAX_PROMPT_LENGTH) {
    throw new functions.https.HttpsError(
      'invalid-argument', 
      `Prompt must be between ${MIN_PROMPT_LENGTH} and ${MAX_PROMPT_LENGTH} characters`
    );
  }
  
  // Check for repeated characters (spam detection)
  const repeatedChars = /(.)\1{9,}/;
  if (repeatedChars.test(trimmedPrompt)) {
    throw new functions.https.HttpsError('invalid-argument', 'Prompt appears to be spam');
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
  
  return { prompt: trimmedPrompt, width, height, steps, guidance_scale };
}

// Main secure image generation function
exports.generateImageSecure = functions
  .runWith({ timeoutSeconds: 300, memory: '1GB' })
  .https.onCall(async (data, context) => {
  
  // Check if user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError(
      'unauthenticated', 
      'You must be logged in to generate images'
    );
  }

  const userId = context.auth.uid;
  const userEmail = context.auth.token.email;
  const clientIp = getClientIp(context.rawRequest);

  // Check if user is blocked
  const blockStatus = await isUserBlocked(userId);
  if (blockStatus.blocked) {
    await sendAlert(
      'Blocked User Attempt',
      `Blocked user ${userEmail} (${userId}) attempted to generate image`,
      'warning'
    );
    throw new functions.https.HttpsError('permission-denied', blockStatus.reason);
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

  // Content moderation
  const moderationResult = await moderateContent(validatedInput.prompt);
  if (!moderationResult.safe) {
    // Log violation
    await admin.firestore().collection('content_violations').add({
      userId,
      userEmail,
      prompt: validatedInput.prompt,
      reason: moderationResult.reason,
      flaggedKeyword: moderationResult.flaggedKeyword,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      ip: clientIp
    });
    
    // Track violations for potential suspension
    const violationsRef = admin.firestore().collection('user_violations').doc(userId);
    await violationsRef.set({
      count: admin.firestore.FieldValue.increment(1),
      lastViolation: admin.firestore.FieldValue.serverTimestamp()
    }, { merge: true });
    
    const violationDoc = await violationsRef.get();
    const violationCount = violationDoc.data()?.count || 0;
    
    if (violationCount >= SUSPICIOUS_ACTIVITY_THRESHOLD) {
      await sendAlert(
        'Multiple Content Violations',
        `User ${userEmail} has ${violationCount} content violations`,
        'critical'
      );
    }
    
    throw new functions.https.HttpsError(
      'invalid-argument',
      'Content violates our usage policies'
    );
  }

  // Check IP rate limit
  const ipRateLimit = await checkIpRateLimit(clientIp, userId);
  if (!ipRateLimit.allowed) {
    throw new functions.https.HttpsError('resource-exhausted', ipRateLimit.reason);
  }

  // User rate limiting with transaction
  const userRef = admin.firestore().collection('users').doc(userId);
  
  try {
    const canProceed = await admin.firestore().runTransaction(async (transaction) => {
      const userDoc = await transaction.get(userRef);
      const now = new Date();
      const today = now.toDateString();
      
      if (userDoc.exists) {
        const userData = userDoc.data();
        
        // Check if user is premium (higher limits)
        const dailyLimit = userData.isPremium ? 50 : DAILY_LIMIT;
        
        if (userData.lastRequestDate === today && userData.requestCount >= dailyLimit) {
          throw new functions.https.HttpsError(
            'resource-exhausted',
            `Daily limit of ${dailyLimit} images reached. ${userData.isPremium ? '' : 'Upgrade to premium for higher limits.'}`
          );
        }
        
        // Update count atomically
        transaction.update(userRef, {
          lastRequestDate: today,
          requestCount: userData.lastRequestDate === today ? userData.requestCount + 1 : 1,
          lastRequestTime: admin.firestore.FieldValue.serverTimestamp(),
          lastIp: clientIp
        });
      } else {
        // Create new user record
        transaction.set(userRef, {
          lastRequestDate: today,
          requestCount: 1,
          createdAt: admin.firestore.FieldValue.serverTimestamp(),
          lastRequestTime: admin.firestore.FieldValue.serverTimestamp(),
          email: userEmail,
          userId: userId,
          lastIp: clientIp,
          isPremium: false
        });
      }
      
      return true;
    });
    
    if (!canProceed) {
      throw new functions.https.HttpsError('internal', 'Rate limit check failed');
    }
    
  } catch (error) {
    if (error.code && error.code.startsWith('functions/')) {
      throw error;
    }
    console.error('Transaction error:', error);
    throw new functions.https.HttpsError('internal', 'Failed to process rate limit');
  }

  // Check if RunPod credentials are configured
  if (!RUNPOD_API_KEY || !RUNPOD_ENDPOINT_ID) {
    console.error('RunPod credentials not configured');
    await sendAlert(
      'Configuration Error',
      'RunPod credentials not configured',
      'critical'
    );
    throw new functions.https.HttpsError(
      'failed-precondition',
      'Service not properly configured. Please contact support.'
    );
  }

  // Monitor costs before generation
  const costStatus = await monitorCosts();

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
      
      // Alert on API errors
      await sendAlert(
        'RunPod API Error',
        `Failed to generate image: ${JSON.stringify(result)}`,
        'error'
      );
      
      throw new functions.https.HttpsError('internal', 'Failed to generate image');
    }

    const processingTime = Date.now() - startTime;

    // Log successful generation
    await admin.firestore().collection('image_generations').add({
      userId,
      userEmail,
      prompt: validatedInput.prompt,
      width: validatedInput.width,
      height: validatedInput.height,
      steps: validatedInput.steps,
      guidanceScale: validatedInput.guidance_scale,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      processingTime,
      success: true,
      ip: clientIp,
      estimatedCost: COST_PER_IMAGE
    });

    // Alert if processing time is unusually high
    if (processingTime > 30000) { // 30 seconds
      await sendAlert(
        'Slow Generation',
        `Image generation took ${processingTime}ms for user ${userEmail}`,
        'warning'
      );
    }

    return {
      success: true,
      image: result.output.image_base64,
      seed: result.output.seed,
      processingTime,
      costStatus: {
        dailyCost: costStatus.dailyCost.toFixed(2),
        monthlyCost: costStatus.monthlyCost.toFixed(2)
      }
    };

  } catch (error) {
    // Log failed generation
    await admin.firestore().collection('image_generations').add({
      userId,
      userEmail,
      prompt: validatedInput.prompt,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      success: false,
      error: error.message,
      ip: clientIp
    }).catch(console.error);

    console.error('Error generating image:', error);
    throw new functions.https.HttpsError('internal', 'Failed to generate image');
  }
});

// Admin function to block/unblock users
exports.manageUser = functions.https.onCall(async (data, context) => {
  // Check if caller is admin
  if (!context.auth || !context.auth.token.admin) {
    throw new functions.https.HttpsError(
      'permission-denied',
      'Only admins can manage users'
    );
  }
  
  const { userId, action, reason, duration } = data;
  
  if (!userId || !action) {
    throw new functions.https.HttpsError('invalid-argument', 'Missing required parameters');
  }
  
  const blockedRef = admin.firestore().collection('blocked_users').doc(userId);
  
  switch (action) {
    case 'block':
      await blockedRef.set({
        blockedAt: admin.firestore.FieldValue.serverTimestamp(),
        blockedBy: context.auth.uid,
        reason: reason || 'Policy violation',
        permanentBan: !duration
      });
      break;
      
    case 'suspend':
      const suspendedUntil = new Date();
      suspendedUntil.setHours(suspendedUntil.getHours() + (duration || 24));
      
      await blockedRef.set({
        suspendedAt: admin.firestore.FieldValue.serverTimestamp(),
        suspendedBy: context.auth.uid,
        suspendedUntil: admin.firestore.Timestamp.fromDate(suspendedUntil),
        reason: reason || 'Temporary suspension'
      });
      break;
      
    case 'unblock':
      await blockedRef.delete();
      break;
      
    default:
      throw new functions.https.HttpsError('invalid-argument', 'Invalid action');
  }
  
  // Send alert
  await sendAlert(
    'User Management Action',
    `Admin ${context.auth.token.email} performed ${action} on user ${userId}`,
    'info'
  );
  
  return { success: true, action, userId };
});

// Scheduled function to clean up old data and check costs
exports.dailyMaintenance = functions.pubsub
  .schedule('0 2 * * *') // Run at 2 AM daily
  .timeZone('America/Los_Angeles')
  .onRun(async (context) => {
    
  // Clean up old IP rate limit records
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  
  const oldIpRecords = await admin.firestore()
    .collection('ip_rate_limits')
    .where('firstSeen', '<', thirtyDaysAgo)
    .get();
    
  const deletePromises = oldIpRecords.docs.map(doc => doc.ref.delete());
  await Promise.all(deletePromises);
  
  console.log(`Cleaned up ${oldIpRecords.size} old IP records`);
  
  // Generate daily cost report
  const costStatus = await monitorCosts();
  
  await admin.firestore().collection('daily_reports').add({
    date: new Date().toDateString(),
    timestamp: admin.firestore.FieldValue.serverTimestamp(),
    dailyCost: costStatus.dailyCost,
    monthlyCost: costStatus.monthlyCost,
    dailyImages: costStatus.dailyImages,
    monthlyImages: costStatus.monthlyImages
  });
  
  return null;
});

// Health check endpoint with detailed status
exports.healthCheck = functions.https.onRequest(async (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '2.0.0',
    features: {
      authentication: true,
      rateLimiting: true,
      contentModeration: true,
      ipTracking: true,
      costMonitoring: true,
      userBlocking: true,
      webhookAlerts: !!ALERT_WEBHOOK_URL
    }
  };
  
  // Check RunPod configuration
  health.runpod = {
    configured: !!(RUNPOD_API_KEY && RUNPOD_ENDPOINT_ID)
  };
  
  res.status(200).json(health);
});