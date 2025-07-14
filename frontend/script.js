const API_URL = 'http://localhost:8000';
let currentJobId = null;
let generationHistory = [];

document.getElementById('generate-btn').addEventListener('click', generateImage);
document.getElementById('download-btn').addEventListener('click', downloadImage);

async function generateImage() {
    const prompt = document.getElementById('prompt').value.trim();
    
    if (!prompt) {
        showStatus('Please enter a prompt', 'error');
        return;
    }
    
    const generateBtn = document.getElementById('generate-btn');
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    
    const requestData = {
        prompt: prompt,
        negative_prompt: document.getElementById('negative-prompt').value,
        width: parseInt(document.getElementById('width').value),
        height: parseInt(document.getElementById('height').value),
        num_inference_steps: parseInt(document.getElementById('steps').value),
        guidance_scale: parseFloat(document.getElementById('guidance').value),
        seed: parseInt(document.getElementById('seed').value)
    };
    
    try {
        const response = await fetch(`${API_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error('Generation failed');
        }
        
        const data = await response.json();
        currentJobId = data.job_id;
        
        showStatus('Generation started. Waiting for result...', 'success');
        pollForResult(currentJobId);
        
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Image';
    }
}

async function pollForResult(jobId) {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_URL}/status/${jobId}`);
            const data = await response.json();
            
            if (data.status === 'completed') {
                clearInterval(pollInterval);
                displayResult(data.result);
                addToHistory(data.result);
                
                const generateBtn = document.getElementById('generate-btn');
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate Image';
                
                showStatus('Image generated successfully!', 'success');
                
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                showStatus(`Generation failed: ${data.error || 'Unknown error'}`, 'error');
                
                const generateBtn = document.getElementById('generate-btn');
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate Image';
            }
            
        } catch (error) {
            clearInterval(pollInterval);
            showStatus(`Error checking status: ${error.message}`, 'error');
            
            const generateBtn = document.getElementById('generate-btn');
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Image';
        }
    }, 2000);
}

function displayResult(result) {
    const resultDiv = document.getElementById('result');
    const img = document.getElementById('generated-image');
    
    img.src = `data:image/png;base64,${result.image_base64}`;
    document.getElementById('image-seed').textContent = result.seed;
    document.getElementById('image-prompt').textContent = result.prompt;
    
    resultDiv.classList.remove('hidden');
}

function addToHistory(result) {
    generationHistory.unshift({
        ...result,
        timestamp: new Date().toISOString()
    });
    
    if (generationHistory.length > 12) {
        generationHistory = generationHistory.slice(0, 12);
    }
    
    updateHistoryDisplay();
}

function updateHistoryDisplay() {
    const historyGrid = document.getElementById('history-grid');
    historyGrid.innerHTML = '';
    
    generationHistory.forEach((item, index) => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <img src="data:image/png;base64,${item.image_base64}" alt="Generated image">
            <p>${item.prompt}</p>
        `;
        
        historyItem.addEventListener('click', () => {
            displayResult(item);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        
        historyGrid.appendChild(historyItem);
    });
}

function downloadImage() {
    const img = document.getElementById('generated-image');
    const link = document.createElement('a');
    link.href = img.src;
    link.download = `ai-generated-${Date.now()}.png`;
    link.click();
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
    statusDiv.classList.remove('hidden');
    
    if (type === 'success') {
        setTimeout(() => {
            statusDiv.classList.add('hidden');
        }, 5000);
    }
}

// For local testing without RunPod
async function testLocalGeneration() {
    const response = await fetch(`${API_URL}/test-local`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt: document.getElementById('prompt').value,
            negative_prompt: document.getElementById('negative-prompt').value,
            width: parseInt(document.getElementById('width').value),
            height: parseInt(document.getElementById('height').value),
            num_inference_steps: parseInt(document.getElementById('steps').value),
            guidance_scale: parseFloat(document.getElementById('guidance').value),
            seed: parseInt(document.getElementById('seed').value)
        })
    });
    
    const result = await response.json();
    displayResult(result);
    addToHistory(result);
    showStatus('Test image generated!', 'success');
}