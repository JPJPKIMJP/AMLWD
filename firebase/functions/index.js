const functions = require('firebase-functions');
const cors = require('cors')({ origin: true });

// Your RunPod credentials (set these in Firebase console)
const RUNPOD_API_KEY = functions.config().runpod?.api_key || process.env.RUNPOD_API_KEY;
const RUNPOD_ENDPOINT_ID = functions.config().runpod?.endpoint_id || process.env.RUNPOD_ENDPOINT_ID;

exports.generateImage = functions.https.onRequest((req, res) => {
  cors(req, res, async () => {
    if (req.method !== 'POST') {
      return res.status(405).send('Method Not Allowed');
    }

    try {
      const { prompt, width = 512, height = 512, steps = 20, guidance_scale = 7.5 } = req.body;

      if (!prompt) {
        return res.status(400).json({ error: 'Prompt is required' });
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
            seed: -1
          }
        })
      });

      const data = await response.json();

      if (data.status === 'COMPLETED' && data.output) {
        res.json({
          success: true,
          image_base64: data.output.image_base64,
          seed: data.output.seed
        });
      } else {
        res.status(500).json({ error: data.error || 'Generation failed' });
      }

    } catch (error) {
      console.error('Error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  });
});