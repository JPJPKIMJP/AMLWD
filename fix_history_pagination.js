// Debug script for history pagination issue
// Run this in browser console

async function debugHistoryPagination() {
    console.log("🔍 Debugging History Pagination...\n");
    
    const db = firebase.firestore();
    const userId = firebase.auth().currentUser?.uid;
    
    if (!userId) {
        console.log("❌ Not logged in");
        return;
    }
    
    // 1. Check total number of images
    const allImages = await db.collection('user_images')
        .where('userId', '==', userId)
        .get();
    
    console.log(`📊 Total images in database: ${allImages.size}`);
    
    // 2. Check if images have proper timestamps
    let missingTimestamps = 0;
    allImages.forEach(doc => {
        if (!doc.data().timestamp) {
            missingTimestamps++;
            console.log(`⚠️ Image ${doc.id} missing timestamp`);
        }
    });
    
    if (missingTimestamps > 0) {
        console.log(`\n⚠️ ${missingTimestamps} images missing timestamps`);
        console.log("This might cause ordering issues. Run fixMissingTimestamps() to fix.");
    }
    
    // 3. Test pagination manually
    console.log("\n📋 Testing pagination (12 images per page):");
    
    try {
        // Page 1
        const page1 = await db.collection('user_images')
            .where('userId', '==', userId)
            .orderBy('timestamp', 'desc')
            .limit(12)
            .get();
        
        console.log(`Page 1: ${page1.size} images`);
        
        if (page1.size === 12) {
            // Try page 2
            const lastDoc = page1.docs[page1.docs.length - 1];
            const page2 = await db.collection('user_images')
                .where('userId', '==', userId)
                .orderBy('timestamp', 'desc')
                .startAfter(lastDoc)
                .limit(12)
                .get();
            
            console.log(`Page 2: ${page2.size} images`);
            console.log(`Has more: ${page2.size === 12}`);
        }
        
    } catch (error) {
        console.error("❌ Pagination error:", error);
        console.log("\n💡 This might be an index issue. Check Firebase Console:");
        console.log("https://console.firebase.google.com/project/amlwd-image-gen/firestore/indexes");
    }
    
    // 4. Check current UI state
    console.log("\n🖥️ Current UI State:");
    console.log("lastImageDoc:", window.lastImageDoc || "null");
    console.log("hasMoreImages:", window.hasMoreImages || false);
    
    // 5. Test the Firebase function directly
    console.log("\n🔧 Testing getUserImages function:");
    try {
        const getUserImages = firebase.functions().httpsCallable('getUserImages');
        const result = await getUserImages({ limit: 12 });
        console.log("Function result:", result.data);
    } catch (error) {
        console.error("Function error:", error);
    }
}

// Function to fix missing timestamps
async function fixMissingTimestamps() {
    const db = firebase.firestore();
    const userId = firebase.auth().currentUser?.uid;
    
    if (!userId) {
        console.log("❌ Not logged in");
        return;
    }
    
    const images = await db.collection('user_images')
        .where('userId', '==', userId)
        .get();
    
    let fixed = 0;
    const batch = db.batch();
    
    images.forEach(doc => {
        if (!doc.data().timestamp) {
            batch.update(doc.ref, {
                timestamp: firebase.firestore.FieldValue.serverTimestamp()
            });
            fixed++;
        }
    });
    
    if (fixed > 0) {
        await batch.commit();
        console.log(`✅ Fixed ${fixed} images with missing timestamps`);
    } else {
        console.log("✅ All images have timestamps");
    }
}

// Function to manually trigger load more
async function manualLoadMore() {
    console.log("🔄 Manually triggering load more...");
    
    // Get the current last image ID from the UI
    const historyEl = document.getElementById('imageHistory');
    const images = historyEl.querySelectorAll('[data-image-id]');
    
    if (images.length === 0) {
        console.log("No images in history");
        return;
    }
    
    const lastImageId = images[images.length - 1].getAttribute('data-image-id');
    console.log("Last image ID:", lastImageId);
    
    // Call the function directly
    const getUserImages = firebase.functions().httpsCallable('getUserImages');
    const result = await getUserImages({ 
        limit: 12, 
        startAfter: lastImageId 
    });
    
    console.log("Load more result:", result.data);
}

// Run the debug
debugHistoryPagination();