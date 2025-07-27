// Constants
const generateBtn = document.getElementById('generateBtn');
const promptInput = document.getElementById('prompt');
const widthInput = document.getElementById('width');
const heightInput = document.getElementById('height');
const stepsInput = document.getElementById('steps');
const guidanceInput = document.getElementById('guidance');
const statusDiv = document.getElementById('status');
const resultDiv = document.getElementById('result');
const generatedImage = document.getElementById('generatedImage');
const downloadBtn = document.getElementById('downloadBtn');
const copyPromptBtn = document.getElementById('copyPromptBtn');

// RunPod Configuration
const RUNPOD_ENDPOINT = 'https://api.runpod.ai/v2/6f3dkzdg44elpj/runsync';
let RUNPOD_API_KEY = localStorage.getItem('runpod_api_key') || '';

// Event Listeners
generateBtn.addEventListener('click', generateImage);
downloadBtn.addEventListener('click', downloadImage);
copyPromptBtn.addEventListener('click', copyPrompt);

// Check for API key on load
window.addEventListener('load', () => {
    if (!RUNPOD_API_KEY) {
        const apiKeyPrompt = prompt('Please enter your RunPod API key:');
        if (apiKeyPrompt) {
            RUNPOD_API_KEY = apiKeyPrompt;
            localStorage.setItem('runpod_api_key', apiKeyPrompt);
        }
    }
});

// Update parameter displays
widthInput.addEventListener('input', (e) => {
    document.getElementById('widthValue').textContent = e.target.value;
});

heightInput.addEventListener('input', (e) => {
    document.getElementById('heightValue').textContent = e.target.value;
});

stepsInput.addEventListener('input', (e) => {
    document.getElementById('stepsValue').textContent = e.target.value;
});

guidanceInput.addEventListener('input', (e) => {
    document.getElementById('guidanceValue').textContent = e.target.value;
});

// Functions
async function generateImage() {
    const prompt = promptInput.value.trim();
    
    if (!prompt) {
        showStatus('Please enter a prompt', 'error');
        return;
    }

    if (!RUNPOD_API_KEY) {
        const apiKeyPrompt = prompt('Please enter your RunPod API key:');
        if (!apiKeyPrompt) {
            showStatus('API key is required', 'error');
            return;
        }
        RUNPOD_API_KEY = apiKeyPrompt;
        localStorage.setItem('runpod_api_key', apiKeyPrompt);
    }

    // Disable generate button
    generateBtn.disabled = true;
    showStatus('Generating image...', 'loading');

    try {
        const response = await fetch(RUNPOD_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${RUNPOD_API_KEY}`
            },
            body: JSON.stringify({
                input: {
                    prompt: prompt,
                    width: parseInt(widthInput.value),
                    height: parseInt(heightInput.value),
                    num_inference_steps: parseInt(stepsInput.value),
                    guidance_scale: parseFloat(guidanceInput.value),
                    num_outputs: 1,
                    scheduler: "DPMSolverMultistep"
                }
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        console.log('RunPod response:', data);

        // Handle different response formats
        if (data.output) {
            let imageData;
            
            if (typeof data.output === 'string') {
                imageData = data.output;
            } else if (Array.isArray(data.output) && data.output.length > 0) {
                imageData = data.output[0];
            } else if (data.output.image) {
                imageData = data.output.image;
            } else if (data.output.images && Array.isArray(data.output.images)) {
                imageData = data.output.images[0];
            }

            if (imageData) {
                displayImage(imageData);
                showStatus('Image generated successfully!', 'success');
            } else {
                throw new Error('No image data in response');
            }
        } else if (data.id) {
            // Handle async response
            showStatus('Processing... Job ID: ' + data.id, 'loading');
            pollForResult(data.id);
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Generation error:', error);
        showStatus(`Error: ${error.message}`, 'error');
        generateBtn.disabled = false;
    }
}

async function pollForResult(jobId) {
    const maxAttempts = 60;
    const pollInterval = 2000;
    let attempts = 0;

    const statusUrl = `https://api.runpod.ai/v2/6f3dkzdg44elpj/status/${jobId}`;

    const checkStatus = async () => {
        try {
            const response = await fetch(statusUrl, {
                headers: {
                    'Authorization': `Bearer ${RUNPOD_API_KEY}`
                }
            });

            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }

            const data = await response.json();
            console.log('Job status:', data);

            if (data.status === 'COMPLETED' && data.output) {
                let imageData;
                
                if (typeof data.output === 'string') {
                    imageData = data.output;
                } else if (Array.isArray(data.output) && data.output.length > 0) {
                    imageData = data.output[0];
                } else if (data.output.image) {
                    imageData = data.output.image;
                } else if (data.output.images && Array.isArray(data.output.images)) {
                    imageData = data.output.images[0];
                }

                if (imageData) {
                    displayImage(imageData);
                    showStatus('Image generated successfully!', 'success');
                } else {
                    throw new Error('No image data in response');
                }
                generateBtn.disabled = false;
            } else if (data.status === 'FAILED') {
                throw new Error(data.error || 'Generation failed');
            } else if (data.status === 'IN_QUEUE' || data.status === 'IN_PROGRESS') {
                attempts++;
                if (attempts >= maxAttempts) {
                    throw new Error('Generation timed out');
                }
                showStatus(`Processing... (${attempts}/${maxAttempts})`, 'loading');
                setTimeout(checkStatus, pollInterval);
            } else {
                throw new Error(`Unknown status: ${data.status}`);
            }
        } catch (error) {
            console.error('Poll error:', error);
            showStatus(`Error: ${error.message}`, 'error');
            generateBtn.disabled = false;
        }
    };

    checkStatus();
}

function displayImage(imageData) {
    // Handle base64 prefix if not present
    if (!imageData.startsWith('data:image')) {
        imageData = `data:image/png;base64,${imageData}`;
    }
    
    generatedImage.src = imageData;
    generatedImage.style.display = 'block';
    resultDiv.style.display = 'block';
    downloadBtn.style.display = 'inline-block';
    copyPromptBtn.style.display = 'inline-block';
}

function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = type;
    statusDiv.style.display = 'block';
    
    if (type === 'success' || type === 'error') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

function downloadImage() {
    const link = document.createElement('a');
    link.download = `amlwd-${Date.now()}.png`;
    link.href = generatedImage.src;
    link.click();
}

function copyPrompt() {
    navigator.clipboard.writeText(promptInput.value).then(() => {
        showStatus('Prompt copied to clipboard!', 'success');
    }).catch(err => {
        showStatus('Failed to copy prompt', 'error');
    });
}