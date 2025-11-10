const fs=require('fs');
const path='frontend/secure_messagerie/src/components/Messages.vue';
let text=fs.readFileSync(path,'utf8');
text=text.replace(/placeholder="[^"]*"/, 'placeholder="Écrire un message…"');
text=text.replace(/<span v-else>[^<]*<\/span>/, '<span v-else>Créer</span>');
fs.writeFileSync(path,text,'utf8');
