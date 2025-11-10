const fs=require('fs');
const path='frontend/secure_messagerie/src/components/MessagesRealtimeNew.vue';
let text=fs.readFileSync(path,'utf8');
const regex=/attachmentError\.value = '((?:\\'|[^'])*)'/;
text=text.replace(regex,"attachmentError.value = 'Sélectionnez une conversation avant d\\'ajouter un fichier.'");
fs.writeFileSync(path,text,'utf8');
