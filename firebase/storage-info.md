# Firebase Storage Management for AMLWD

## Current Storage Implementation

### How it works:
1. **Image Generation**: When a user generates an image, it's immediately displayed
2. **Automatic Upload**: The `saveToHistory()` function uploads the base64 image to Firebase Storage
3. **Organized by User**: Each user has their own folder: `images/{userId}/`
4. **Metadata in Firestore**: Image URLs and metadata stored in `user_images` collection

### Storage Structure:
```
Firebase Storage (amlwd-image-gen.firebasestorage.app):
└── images/
    └── {userId}/
        └── {timestamp}_{randomId}.png

Firestore:
└── user_images/
    └── {documentId}
        ├── userId: "abc123"
        ├── imageUrl: "https://storage.googleapis.com/..."
        ├── prompt: "user's prompt"
        ├── timestamp: Timestamp
        └── metadata: {width, height, steps, guidanceScale}
```

### Features:
- **Automatic Upload**: Images uploaded immediately after generation
- **Public Access**: Images are made public for easy viewing
- **History Display**: Shows thumbnails with click to view full-size
- **Re-generate Button**: Quick re-generation with same prompt
- **Error Handling**: Fallback display if image unavailable

### Storage Limits & Costs:
- **Free Tier**: 
  - 5GB storage
  - 1GB/day bandwidth
  - 50,000/day downloads
- **Blaze Plan** (pay as you go):
  - $0.026/GB storage per month
  - $0.12/GB download bandwidth
  - No operation limits

### To Monitor Storage:
1. Visit: https://console.firebase.google.com/project/amlwd-image-gen/storage
2. Check "Usage" tab for current storage amount
3. Set up budget alerts in Google Cloud Console

### Future Improvements:
1. Add image compression before upload
2. Implement cleanup policy for old images (30+ days)
3. Add user storage quotas
4. Optimize image format (WebP instead of PNG)