#!/usr/bin/env python3
"""
Find mix4.safetensor in Firebase Storage
"""

import firebase_admin
from firebase_admin import credentials, storage, firestore
import os
from datetime import datetime

# Initialize Firebase
if not firebase_admin._apps:
    # Use environment variable or service account
    if os.path.exists('firebase-service-account.json'):
        cred = credentials.Certificate('firebase-service-account.json')
    else:
        cred = credentials.ApplicationDefault()
    
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'amlwd-image-gen.firebasestorage.app'
    })

# Get Firestore and Storage references
db = firestore.client()
bucket = storage.bucket()

print("🔍 Searching for mix4.safetensor...\n")

# 1. Check Firestore for LoRA records
print("📄 Checking Firestore user_loras collection:")
loras_ref = db.collection('user_loras')
docs = loras_ref.stream()

found_in_firestore = False
for doc in docs:
    data = doc.to_dict()
    filename = data.get('filename', '')
    if 'mix4' in filename.lower():
        found_in_firestore = True
        print(f"\n✅ Found in Firestore:")
        print(f"   Document ID: {doc.id}")
        print(f"   Filename: {filename}")
        print(f"   URL: {data.get('downloadURL', 'No URL')}")
        print(f"   User: {data.get('userId', 'Unknown')}")
        print(f"   Uploaded: {data.get('uploadedAt', 'Unknown')}")
        print(f"   Synced: {data.get('syncedToRunPod', False)}")

if not found_in_firestore:
    print("   ❌ Not found in Firestore")

# 2. Check Storage directly
print("\n📦 Checking Firebase Storage:")
# List all files in loras/ directory
blobs = bucket.list_blobs(prefix='loras/')

found_in_storage = False
for blob in blobs:
    if 'mix4' in blob.name.lower():
        found_in_storage = True
        print(f"\n✅ Found in Storage:")
        print(f"   Path: {blob.name}")
        print(f"   Size: {blob.size / (1024*1024):.2f} MB")
        print(f"   Created: {blob.time_created}")
        print(f"   Public URL: {blob.public_url}")
        
        # Generate signed URL
        from datetime import timedelta
        url = blob.generate_signed_url(timedelta(hours=24))
        print(f"   Download URL (24h): {url}")
        
        # Generate wget command
        filename = os.path.basename(blob.name)
        print(f"\n📋 Manual sync command:")
        print(f"   wget -O /workspace/ComfyUI/models/loras/{filename} '{url}'")

if not found_in_storage:
    print("   ❌ Not found in Storage")

# 3. Search for similar names
print("\n🔍 Searching for similar LoRA files:")
print("\nIn Firestore:")
docs = loras_ref.stream()
for doc in docs:
    data = doc.to_dict()
    filename = data.get('filename', '')
    if filename.endswith('.safetensors'):
        print(f"   - {filename}")

print("\nIn Storage:")
blobs = bucket.list_blobs(prefix='loras/')
for blob in blobs:
    if blob.name.endswith('.safetensors'):
        print(f"   - {os.path.basename(blob.name)}")

print("\n💡 If mix4.safetensor was just uploaded:")
print("1. It might not be in the user_loras collection yet")
print("2. Check the upload page for the wget command")
print("3. Or add it to known_loras in flux_handler.py")