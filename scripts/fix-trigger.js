const fs=require('fs');
const path='frontend/secure_messagerie/src/components/MessagesRealtimeNew.vue';
let text=fs.readFileSync(path,'utf8');
const start=text.indexOf('function triggerAttachmentPicker() {');
const end=text.indexOf('function onAttachmentChange', start);
if(start===-1 || end===-1){ throw new Error('markers missing'); }
const block=[
  'function triggerAttachmentPicker() {',
  "  attachmentError.value = ''",
  "  if (!selectedConversationId.value) {",
  "    attachmentError.value = 'Sélectionnez une conversation avant d\\'ajouter un fichier.'",
  '    return',
  '  }',
  '  if (attachmentInput.value) {',
  "    attachmentInput.value.value = ''",
  '    attachmentInput.value.click()',
  '  }',
  '}',
  ''
].join('\n');
text=text.slice(0,start)+block+text.slice(end);
fs.writeFileSync(path,text,'utf8');
