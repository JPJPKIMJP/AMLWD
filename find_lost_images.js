// Script to find lost generated images
// Run this in the browser console while logged into the app

async function findLostImages() {
    console.log("🔍 Searching for lost generated images...\n");
    
    const db = firebase.firestore();
    const userId = firebase.auth().currentUser?.uid;
    
    if (!userId) {
        console.log("❌ Not logged in");
        return;
    }
    
    // 1. Check image_generations collection (log of all attempts)
    console.log("📊 Checking generation logs...");
    const generationsSnapshot = await db.collection('image_generations')
        .where('userId', '==', userId)
        .where('success', '==', true)
        .orderBy('timestamp', 'desc')
        .limit(50)
        .get();
    
    console.log(`Found ${generationsSnapshot.size} successful generations in logs`);
    
    // 2. Check user_images collection (what shows in history)
    const imagesSnapshot = await db.collection('user_images')
        .where('userId', '==', userId)
        .orderBy('timestamp', 'desc')
        .limit(50)
        .get();
    
    console.log(`Found ${imagesSnapshot.size} images in history\n`);
    
    // 3. Find discrepancies
    const generations = [];
    generationsSnapshot.forEach(doc => {
        const data = doc.data();
        generations.push({
            id: doc.id,
            prompt: data.prompt,
            timestamp: data.timestamp?.toDate() || new Date(),
            savedUrls: data.savedImageUrls || [],
            processingTime: data.processingTime
        });
    });
    
    const savedImages = new Set();
    imagesSnapshot.forEach(doc => {
        const data = doc.data();
        savedImages.add(data.prompt);
    });
    
    // 4. Find lost images
    console.log("🚨 Lost Images (generated but not in history):");
    const lost = [];
    generations.forEach(gen => {
        if (!savedImages.has(gen.prompt)) {
            lost.push(gen);
            console.log(`\n❌ Lost: "${gen.prompt.substring(0, 50)}..."`);
            console.log(`   Generated: ${gen.timestamp.toLocaleString()}`);
            console.log(`   Processing time: ${gen.processingTime}ms`);
            if (gen.savedUrls.length > 0) {
                console.log(`   URLs were saved: ${gen.savedUrls.join(', ')}`);
            }
        }
    });
    
    console.log(`\n📊 Summary: ${lost.length} images lost out of ${generations.length} generations`);
    
    // 5. Check for orphaned Firebase Storage files
    console.log("\n📦 Checking Firebase Storage for orphaned files...");
    const storage = firebase.storage();
    const storageRef = storage.ref('images/' + userId);
    
    try {
        const listResult = await storageRef.listAll();
        console.log(`Found ${listResult.items.length} files in storage for this user`);
        
        // Check if these files have corresponding Firestore entries
        const orphaned = [];
        for (const item of listResult.items) {
            const url = await item.getDownloadURL();
            const hasEntry = await db.collection('user_images')
                .where('userId', '==', userId)
                .where('imageUrl', '==', url)
                .limit(1)
                .get();
            
            if (hasEntry.empty) {
                orphaned.push({
                    name: item.name,
                    url: url,
                    path: item.fullPath
                });
            }
        }
        
        if (orphaned.length > 0) {
            console.log(`\n🗂️ Found ${orphaned.length} orphaned files in storage:`);
            orphaned.forEach(file => {
                console.log(`   - ${file.name}`);
            });
        }
    } catch (error) {
        console.log("⚠️ Could not list storage files:", error.message);
    }
    
    return { lost, generations };
}

// Function to recover lost images from generation logs
async function recoverLostImages() {
    console.log("\n🔧 Attempting to recover lost images...");
    
    const db = firebase.firestore();
    const userId = firebase.auth().currentUser?.uid;
    
    if (!userId) {
        console.log("❌ Not logged in");
        return;
    }
    
    // Get all successful generations
    const generationsSnapshot = await db.collection('image_generations')
        .where('userId', '==', userId)
        .where('success', '==', true)
        .orderBy('timestamp', 'desc')
        .get();
    
    // Get all saved images
    const imagesSnapshot = await db.collection('user_images')
        .where('userId', '==', userId)
        .get();
    
    const savedPrompts = new Set();
    imagesSnapshot.forEach(doc => {
        savedPrompts.add(doc.data().prompt);
    });
    
    // Recover lost ones
    let recovered = 0;
    const batch = db.batch();
    
    generationsSnapshot.forEach(doc => {
        const data = doc.data();
        if (!savedPrompts.has(data.prompt) && data.savedImageUrls?.length > 0) {
            // Create user_images entry
            const imageRef = db.collection('user_images').doc();
            batch.set(imageRef, {
                userId: userId,
                userEmail: data.userEmail,
                prompt: data.prompt,
                imageUrl: data.savedImageUrls[0],
                fileName: `recovered_${Date.now()}_${recovered}.png`,
                size: 0, // Unknown
                timestamp: data.timestamp,
                metadata: {
                    width: data.width,
                    height: data.height,
                    steps: data.steps,
                    guidanceScale: data.guidanceScale,
                    recovered: true
                }
            });
            recovered++;
        }
    });
    
    if (recovered > 0) {
        await batch.commit();
        console.log(`✅ Recovered ${recovered} lost images!`);
        console.log("Refresh the page to see them in history.");
    } else {
        console.log("No images to recover with saved URLs");
    }
}

// Run the search
findLostImages().then(result => {
    if (result && result.lost.length > 0) {
        console.log("\n💡 To recover images with saved URLs, run: recoverLostImages()");
    }
});