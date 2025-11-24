// Script utilitaire pour lister les noms exportables depuis useMessagesView.js
// Usage: node list_exports.js

const fs = require("fs");
const path = require("path");

const sourcePath = path.join(
  "frontend",
  "secure_messagerie",
  "src",
  "views",
  "messages",
  "useMessagesView.js"
);
const lines = fs.readFileSync(sourcePath, "utf8").split(/\r?\n/);

function collectNames(lines) {
  const names = new Set();

  // --- Parse les destructurations multi-lignes ---
  function consumeDestructure(start) {
    let buffer = "";
    let depth = 0;
    let end = start;
    for (let i = start; i < lines.length; i++) {
      const line = lines[i];
      buffer += line + "\n";
      depth += (line.match(/\{/g) || []).length;
      depth -= (line.match(/\}/g) || []).length;
      if (depth <= 0) {
        end = i;
        break;
      }
    }
    const startIdx = buffer.indexOf("{") + 1;
    const endIdx = buffer.lastIndexOf("}");
    if (startIdx <= 0 || endIdx <= startIdx) {
      return { names: [], end };
    }
    const inner = buffer.slice(startIdx, endIdx);
    const tokens = inner.split(",");
    const extracted = [];
    for (const raw of tokens) {
      let token = raw.trim();
      if (!token) continue;
      if (token.startsWith("//")) continue;
      if (token.startsWith("...")) token = token.slice(3).trim();
      if (!token) continue;
      if (token.includes(":")) token = token.split(":").pop().trim();
      if (token.includes("=")) token = token.split("=")[0].trim();
      if (token) extracted.push(token);
    }
    return { names: extracted, end };
  }

  // --- Collecte les variables/fonctions declares en surface ---
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trimStart();
    const indent = line.length - trimmed.length;

    // Destructurations de premier niveau
    if (
      trimmed.startsWith("const {") ||
      trimmed.startsWith("let {") ||
      trimmed.startsWith("var {")
    ) {
      if (indent > 0 && indent <= 2) {
        const result = consumeDestructure(i);
        result.names.forEach((name) => names.add(name));
        i = result.end;
      }
      continue;
    }

    // Declarations simples
    if (
      trimmed.startsWith("const ") ||
      trimmed.startsWith("let ") ||
      trimmed.startsWith("var ")
    ) {
      if (indent > 0 && indent <= 2) {
        const match = trimmed.match(/^(?:const|let|var)\s+([A-Za-z0-9_$]+)/);
        if (match) names.add(match[1]);
      }
      continue;
    }

    // Fonctions nommees
    if (
      trimmed.startsWith("async function ") ||
      trimmed.startsWith("function ")
    ) {
      if (indent > 0 && indent <= 2) {
        const match = trimmed.match(
          /^(?:async\s+)?function\s+([A-Za-z0-9_$]+)/
        );
        if (match) names.add(match[1]);
      }
    }
  }

  return Array.from(names).sort((a, b) => a.localeCompare(b));
}

const names = collectNames(lines);
console.log(names.join("\n"));
