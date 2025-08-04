const admin = require('firebase-admin');
const serviceAccount = require('./firebase/service-account-key.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  storageBucket: 'amlwd-image-gen.firebasestorage.app'
});

const bucket = admin.storage().bucket();

async function listLoras() {
  console.log('Listing LoRA files in Firebase Storage:');
  console.log('-'.repeat(50));
  
  const [files] = await bucket.getFiles({ prefix: 'loras/' });
  
  if (files.length === 0) {
    console.log('No LoRA files found in Firebase Storage');
    return;
  }
  
  for (const file of files) {
    const [metadata] = await file.getMetadata();
    const sizeMB = (metadata.size / 1024 / 1024).toFixed(1);
    const uploaded = new Date(metadata.timeCreated).toLocaleString();
    
    console.log(`\nFile: ${file.name}`);
    console.log(`  Size: ${sizeMB} MB`);
    console.log(`  Uploaded: ${uploaded}`);
    console.log(`  ContentType: ${metadata.contentType}`);
    
    // Get download URL
    try {
      const [url] = await file.getSignedUrl({
        action: 'read',
        expires: Date.now() + 3600 * 1000 // 1 hour
      });
      console.log(`  URL: ${url.substring(0, 100)}...`);
    } catch (e) {
      console.log('  URL: Could not generate signed URL');
    }
  }
  
  console.log(`\nTotal LoRA files: ${files.length}`);
}

listLoras().then(() => process.exit(0)).catch(err => {
  console.error('Error:', err);
  process.exit(1);
});