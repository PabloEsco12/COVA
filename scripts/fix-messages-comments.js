const fs=require('fs');
const path='frontend/secure_messagerie/src/components/Messages.vue';
let text=fs.readFileSync(path,'utf8');
text=text.replace(/\/\/ R[^\n]*\n/, "// Récupère les messages d'une conversation\n");
text=text.replace(/\/\/\s*Adapter[^\n]*\n/, "    // Adapter selon le format de réponse réel de l’API\n");
text=text.replace(/\/\/\s*Scrolle[^\n]*\n/, "    // Scrolle en bas après chargement\n");
fs.writeFileSync(path,text,'utf8');
