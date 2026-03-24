const { createCanvas, loadImage } = require('canvas');
const fs = require('fs');

async function addOverlay(imagePath, text, outputPath) {
    try {
        console.log(`Processing: ${imagePath} -> ${outputPath}`);
        
        const image = await loadImage(imagePath);
        const canvas = createCanvas(image.width, image.height);
        const ctx = canvas.getContext('2d');
        
        // Draw original image
        ctx.drawImage(image, 0, 0);
        
        // Add semi-transparent background for text
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 50, canvas.width, 200);
        
        // Add text overlay
        ctx.fillStyle = 'white';
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 2;
        ctx.font = 'bold 64px Arial';
        ctx.textAlign = 'center';
        
        // Wrap text
        const lines = wrapText(ctx, text, canvas.width * 0.9);
        const lineHeight = 80;
        const startY = 120;
        
        lines.forEach((line, index) => {
            const y = startY + (index * lineHeight);
            ctx.strokeText(line, canvas.width/2, y);
            ctx.fillText(line, canvas.width/2, y);
        });
        
        // Save as PNG
        const buffer = canvas.toBuffer('image/png');
        fs.writeFileSync(outputPath, buffer);
        console.log(`✅ Created: ${outputPath}`);
        
    } catch (error) {
        console.error(`❌ Error: ${error.message}`);
    }
}

function wrapText(ctx, text, maxWidth) {
    const words = text.split(' ');
    const lines = [];
    let currentLine = words[0];
    
    for (let i = 1; i < words.length; i++) {
        const word = words[i];
        const width = ctx.measureText(currentLine + ' ' + word).width;
        if (width < maxWidth) {
            currentLine += ' ' + word;
        } else {
            lines.push(currentLine);
            currentLine = word;
        }
    }
    lines.push(currentLine);
    return lines;
}

// Create slideshow
async function createSlideshow() {
    const hooks = [
        "Villa that costs LESS per person than a hotel room! 🏖️",
        "22 friends split this Greek paradise",
        "15 minutes from Athens airport ✈️",
        "Private infinity pool & sea views 🌊",
        "Book Villa Lithos Porto Rafti now!"
    ];
    
    console.log('🎨 Creating Villa Lithos slideshow...\n');
    
    for (let i = 0; i < hooks.length; i++) {
        const inputFile = 'slide-01.jpg'; // Same image for all slides
        const outputFile = `final-${String(i+1).padStart(2, '0')}.png`;
        
        await addOverlay(inputFile, hooks[i], outputFile);
        
        // Add small delay
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.log('\n🎉 Slideshow created! Files:');
    const files = fs.readdirSync('.').filter(f => f.startsWith('final-'));
    files.forEach(f => console.log(`  📸 ${f}`));
}

createSlideshow();