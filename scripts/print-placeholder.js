const fs=require('fs');
const text=fs.readFileSync('frontend/secure_messagerie/src/components/Messages.vue','utf8');
const match=text.match(/placeholder="([^\"]*)"/);
console.log(match[1]);
