/* Render/static-site build: resolve index.html from this file's directory (not process.cwd()). */
const fs = require('fs');
const path = require('path');
const indexPath = path.join(__dirname, 'index.html');
if (!fs.existsSync(indexPath)) {
    console.error('glb-noir build: missing', indexPath);
    process.exit(1);
}
console.log('glb-noir: static HTML ok');
