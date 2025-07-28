// Quick script to sync mix4.safetensor to RunPod
// Run this in browser console on the Firebase app

async function findAndSyncMix4() {
    const db = firebase.firestore();
    const storage = firebase.storage();
    
    console.log("🔍 Looking for mix4.safetensor...");
    
    // 1. Check user_loras collection
    const lorasSnapshot = await db.collection('user_loras')
        .where('userId', '==', firebase.auth().currentUser.uid)
        .get();
    
    let mix4Doc = null;
    lorasSnapshot.forEach(doc => {
        const data = doc.data();
        if (data.filename && data.filename.includes('mix4')) {
            mix4Doc = { id: doc.id, ...data };
            console.log("✅ Found in Firestore:", data.filename);
        }
    });
    
    if (mix4Doc) {
        console.log("📋 LoRA Details:");
        console.log("   Filename:", mix4Doc.filename);
        console.log("   URL:", mix4Doc.downloadURL);
        console.log("   Synced:", mix4Doc.syncedToRunPod || false);
        
        // Generate wget command
        console.log("\n📋 Manual sync command:");
        console.log(`wget -O /workspace/ComfyUI/models/loras/${mix4Doc.filename} "${mix4Doc.downloadURL}"`);
        
        // Try auto-sync
        if (!mix4Doc.syncedToRunPod) {
            console.log("\n🚀 Attempting auto-sync...");
            try {
                const syncLoraToRunPod = firebase.functions().httpsCallable('syncLoraToRunPod');
                const result = await syncLoraToRunPod({
                    downloadURL: mix4Doc.downloadURL,
                    filename: mix4Doc.filename,
                    docId: mix4Doc.id
                });
                console.log("✅ Sync result:", result.data);
            } catch (error) {
                console.log("❌ Auto-sync failed:", error.message);
                console.log("Use the wget command above to manually sync");
            }
        }
        
        return mix4Doc;
    }
    
    // 2. If not in Firestore, check Storage directly
    console.log("\n📦 Checking Storage directly...");
    const listRef = storage.ref('loras/');
    const res = await listRef.listAll();
    
    for (const item of res.items) {
        if (item.name.includes('mix4')) {
            console.log("✅ Found in Storage:", item.name);
            const url = await item.getDownloadURL();
            console.log("   Download URL:", url);
            console.log("\n📋 Manual sync command:");
            console.log(`wget -O /workspace/ComfyUI/models/loras/${item.name.split('/').pop()} "${url}"`);
            
            // Add the URL to flux_handler.py known_loras
            console.log("\n📝 Add this to flux_handler.py known_loras:");
            console.log(`"mix4": "${url}"`);
            
            return { filename: item.name, downloadURL: url };
        }
    }
    
    console.log("❌ mix4.safetensor not found");
    console.log("\n💡 To upload a new LoRA:");
    console.log("1. Go to /lora-upload.html");
    console.log("2. Or use /lora-upload-enhanced.html for auto-sync");
}

// Run it
findAndSyncMix4();