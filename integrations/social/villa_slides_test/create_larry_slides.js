
const { createCanvas, loadImage } = require('canvas');
const fs = require('fs');

const slideStructure = [{"slide": 1, "purpose": "Hook + Setup - Stop the scroll", "text": "Villa that costs LESS per person than a hotel room", "visual_focus": "exterior_shocking_price"}, {"slide": 2, "purpose": "Challenge/Problem - Create tension", "text": "Everyone thinks luxury villas\\nare only for the rich...", "visual_focus": "expensive_looking_exterior"}, {"slide": 3, "purpose": "Solution Introduction - Present the solution", "text": "But when 22 friends\\nsplit Villa Lithos...", "visual_focus": "group_capacity_visual"}, {"slide": 4, "purpose": "Transformation/Result - Show the wow", "text": "You get luxury for LESS\\nthan a hotel room! \ud83e\udd2f", "visual_focus": "luxury_amenities_pool"}, {"slide": 5, "purpose": "Reaction/Validation - Social proof", "text": "15 minutes from Athens airport\\nFeels like private paradise \u2708\ufe0f", "visual_focus": "sunset_infinity_pool"}, {"slide": 6, "purpose": "CTA + Brand", "text": "Book Villa Lithos Porto Rafti\\nLink in bio \ud83c\udfd6\ufe0f", "visual_focus": "best_result_with_branding"}];

async function createLarrySlide(imagePath, slideData, outputPath) {
    try {
        const image = await loadImage(imagePath);
        const canvas = createCanvas(1080, 1920); // TikTok format
        const ctx = canvas.getContext('2d');
        
        // Draw background image (resized to fit)
        const aspectRatio = image.width / image.height;
        let drawWidth = canvas.width;
        let drawHeight = canvas.width / aspectRatio;
        
        if (drawHeight > canvas.height) {
            drawHeight = canvas.height;
            drawWidth = canvas.height * aspectRatio;
        }
        
        const offsetX = (canvas.width - drawWidth) / 2;
        const offsetY = (canvas.height - drawHeight) / 2;
        
        ctx.drawImage(image, offsetX, offsetY, drawWidth, drawHeight);
        
        // Add semi-transparent background for text (Larry style)
        const textAreaHeight = 200;
        const textAreaY = canvas.height * 0.15; // 28% from top (Larry rule)
        
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, textAreaY - 20, canvas.width, textAreaHeight);
        
        // Larry text formatting
        ctx.fillStyle = 'white';
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 4;  // Thick black outline
        ctx.font = 'bold 56px Arial';
        ctx.textAlign = 'center';
        
        // Manual line breaks (Larry rule: 4-6 words per line)
        const lines = slideData.text.split('\\n');
        const lineHeight = 70;
        const startY = textAreaY + 60;
        
        lines.forEach((line, index) => {
            const y = startY + (index * lineHeight);
            ctx.strokeText(line, canvas.width/2, y);
            ctx.fillText(line, canvas.width/2, y);
        });
        
        // Add slide number (small, bottom corner)
        ctx.font = '20px Arial';
        ctx.fillStyle = 'rgba(255,255,255,0.8)';
        ctx.fillText(`${slideData.slide}/6`, canvas.width - 50, canvas.height - 30);
        
        const buffer = canvas.toBuffer('image/png');
        fs.writeFileSync(outputPath, buffer);
        console.log(`✅ Created Larry slide ${slideData.slide}: ${outputPath}`);
        
    } catch (error) {
        console.error(`❌ Error creating slide: ${error.message}`);
    }
}

async function createAllSlides() {
    console.log('🎨 Creating Larry-style Villa Lithos slides...\n');
    
    const baseImage = 'slide-01.jpg'; // Use same villa image for all
    
    for (let i = 0; i < slideStructure.length; i++) {
        const slideData = slideStructure[i];
        const outputFile = `larry-slide-${String(i+1).padStart(2, '0')}.png`;
        
        await createLarrySlide(baseImage, slideData, outputFile);
        await new Promise(resolve => setTimeout(resolve, 200)); // Small delay
    }
    
    console.log('\n🎉 All Larry slides created!');
    const files = fs.readdirSync('.').filter(f => f.startsWith('larry-slide-'));
    files.forEach(f => console.log(`  📸 ${f}`));
}

createAllSlides();
