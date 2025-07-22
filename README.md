# AMLWD - Full-Stack AI Image Generation Platform

A complete AI image generation platform with RunPod serverless backend, REST API, and modern web interface.

> **🔒 Security**: This project uses secure authentication. Visit https://amlwd-image-gen.web.app/secure.html for the authenticated version.

## Architecture

```
AMLWD/
├── frontend/          # React-like web interface
├── backend/           # FastAPI REST API
├── runpod/           # RunPod serverless handler
└── docker-compose.yml # Local development
```

## Features

- **Full-Stack Solution**: Web UI + API + RunPod serverless
- **Modern Web Interface**: Responsive design with real-time generation
- **REST API**: FastAPI backend with async job processing
- **RunPod Integration**: Serverless GPU inference
- **Local Development**: Docker Compose setup
- **Image History**: Track and revisit previous generations

## Quick Start

### 1. Local Development

```bash
# Clone the repository
git clone https://github.com/JPJPKIMJP/AMLWD.git
cd AMLWD

# Copy environment variables
cp .env.example .env
# Edit .env with your RunPod credentials

# Start all services
docker-compose up

# Visit http://localhost:3000
```

### 2. Deploy RunPod Serverless

```bash
# Build and push RunPod image
cd runpod
docker build -t your-dockerhub-username/amlwd-runpod:latest .
docker push your-dockerhub-username/amlwd-runpod:latest
```

Then create RunPod endpoint with your image.

### 3. Deploy Backend & Frontend

**Backend (any cloud provider):**
```bash
cd backend
docker build -t your-username/amlwd-backend:latest .
# Deploy to your preferred platform
```

**Frontend (static hosting):**
```bash
cd frontend
# Update API_URL in script.js to your backend URL
# Deploy to Vercel, Netlify, or any static host
```

## API Endpoints

### Backend API

- `GET /` - API info
- `POST /generate` - Start image generation
- `GET /status/{job_id}` - Check generation status
- `GET /jobs` - List all jobs
- `POST /test-local` - Test without RunPod

### Input Format

```json
{
  "input": {
    "prompt": "a beautiful sunset over mountains",
    "negative_prompt": "ugly, blurry, low quality",
    "width": 512,
    "height": 512,
    "num_inference_steps": 20,
    "guidance_scale": 7.5,
    "seed": -1
  }
}
```

### 4. Output Format

```json
{
  "output": {
    "image_base64": "iVBORw0KGgoAAAANS...",
    "seed": 42,
    "prompt": "a beautiful sunset over mountains",
    "width": 512,
    "height": 512
  }
}
```

## Local Testing

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install runpod
   ```

2. Test handler locally:
   ```python
   from src.handler import handler
   import json
   
   with open('test_input.json') as f:
       test_job = json.load(f)
   
   result = handler(test_job)
   print(result)
   ```

## Configuration

### Environment Variables

- `MODEL_ID`: Hugging Face model ID (default: `runwayml/stable-diffusion-v1-5`)
  - Examples: `stabilityai/stable-diffusion-2-1`, `prompthero/openjourney`

### Supported Parameters

- `prompt` (required): Text description of desired image
- `negative_prompt`: What to avoid in the image
- `width`: Image width (default: 512)
- `height`: Image height (default: 512)
- `num_inference_steps`: Quality/speed tradeoff (default: 20)
- `guidance_scale`: Prompt adherence (default: 7.5)
- `seed`: Reproducibility (-1 for random)

## GitHub Actions (Optional)

The `.github/workflows/docker-build.yml` will automatically build and push your Docker image on every push to main branch.

## Cost Optimization

- Use fewer inference steps (15-20) for faster generation
- Smaller images (512x512) generate faster
- Consider using A4000 GPUs for cost/performance balance

## Troubleshooting

1. **Out of Memory**: Reduce image size or batch size
2. **Slow Generation**: Reduce inference steps or use smaller model
3. **Poor Quality**: Increase inference steps or guidance scale

## Production Deployment

### Complete Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│   RunPod    │
│  (Static)   │     │   (API)     │     │ (Serverless)│
└─────────────┘     └─────────────┘     └─────────────┘
```

1. **Frontend**: Deploy to Vercel/Netlify (free tier available)
2. **Backend**: Deploy to Railway/Render ($5-10/month)
3. **RunPod**: Pay per generation (~$0.0003/sec)

### Firebase Deployment

This project includes Firebase hosting and functions support:

- **Live URL**: https://amlwd-image-gen.web.app
- **API Endpoint**: https://amlwd-image-gen.web.app/api
- **Project ID**: amlwd-image-gen

See `firebase-config.json` for complete Firebase configuration details.

### Security

- Add authentication to backend
- Use environment variables for all secrets
- Enable CORS for your domain only
- Rate limit API endpoints

## License

MIT
