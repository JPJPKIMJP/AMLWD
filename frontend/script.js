const API_URL = 'http://localhost:8000';

document.getElementById('generate-btn').addEventListener('click', generateImage);

async function generateImage() {
    const prompt = document.getElementById('prompt').value.trim();
    const generateBtn = document.getElementById('generate-btn');
    const status = document.getElementById('status');
    const output = document.getElementById('output');
    
    if (!prompt) {
        showStatus('Please enter a prompt', 'error');
        return;
    }
    
    // Disable button and show loading
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    showStatus('Starting image generation...', 'loading');
    output.classList.remove('show');
    
    try {
        // Use real generation endpoint
        const response = await fetch(`${API_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                width: 512,
                height: 512,
                num_inference_steps: 20,
                guidance_scale: 7.5
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to start generation');
        }
        
        const data = await response.json();
        
        // Handle job-based response
        if (data.job_id) {
            const jobId = data.job_id;
            showStatus('Generating image... This may take 30-60 seconds', 'loading');
            await pollForResult(jobId);
        } else if (data.image_base64) {
            // Direct response (shouldn't happen with RunPod)
            displayImage(data);
            showStatus('Image generated successfully!', 'success');
            setTimeout(hideStatus, 3000);
        }
        
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate';
    }
}

async function pollForResult(jobId) {
    const maxAttempts = 60; // 2 minutes max
    let attempts = 0;
    
    while (attempts < maxAttempts) {
        try {
            const response = await fetch(`${API_URL}/status/${jobId}`);
            const data = await response.json();
            
            if (data.status === 'completed') {
                displayImage(data.result);
                hideStatus();
                return;
            } else if (data.status === 'failed') {
                throw new Error(data.error || 'Generation failed');
            }
            
            // Wait 2 seconds before next poll
            await new Promise(resolve => setTimeout(resolve, 2000));
            attempts++;
            
        } catch (error) {
            throw error;
        }
    }
    
    throw new Error('Generation timed out');
}

function displayImage(result) {
    const output = document.getElementById('output');
    const img = document.getElementById('generated-image');
    
    img.src = `data:image/png;base64,${result.image_base64}`;
    output.classList.add('show');
}

function showStatus(message, type) {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = `status show ${type}`;
}

function hideStatus() {
    const status = document.getElementById('status');
    status.classList.remove('show');
}

// For testing without backend
async function testGeneration() {
    showStatus('Generating test image...', 'loading');
    
    // Simulate delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Display a placeholder image
    const placeholderImage = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==';
    displayImage({ image_base64: placeholderImage });
    hideStatus();
}