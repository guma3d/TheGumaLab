
const fs = require('fs');
const html = fs.readFileSync('YoutubeToDoc/templates/index.html', 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
    console.log('No script tag found!');
    process.exit(1);
}
let scriptContent = scriptMatch[1];
// Mock browser objects
const code = \
const window = { location: { pathname: '/' } };
const document = { addEventListener: () => {} };
\ + scriptContent;

try {
    // Just syntax check, don't execute
    new Function(code);
    console.log('Syntax OK!');
} catch (e) {
    console.log('Syntax Error:', e.message);
}

