const fs = require('fs');
const path = require('path');

// Liste des fichiers à corriger
const files = [
  'ProfileSettings.tsx',
  'SecuritySettings.tsx',
  'SystemSettings.tsx',
  'InterfaceSettings.tsx',
  'PrivacySettings.tsx'
];

files.forEach(file => {
  const filePath = path.join(__dirname, file);
  
  if (fs.existsSync(filePath)) {
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Ajouter l'import ElementType si pas présent
    if (!content.includes("import { ElementType }") && !content.includes("ElementType } from 'react'")) {
      // Trouver la dernière ligne d'import react-icons
      const lastIconImport = content.lastIndexOf("} from 'react-icons/fi';");
      if (lastIconImport !== -1) {
        const insertPosition = lastIconImport + "} from 'react-icons/fi';".length;
        content = content.slice(0, insertPosition) + "\nimport { ElementType } from 'react';" + content.slice(insertPosition);
      }
    }
    
    // Remplacer toutes les utilisations d'icônes
    // Pattern 1: <Icon as={FiIcon} 
    content = content.replace(/as=\{(Fi\w+)\}/g, 'as={$1 as ElementType}');
    
    // Pattern 2: icon={<Icon as={FiIcon} 
    content = content.replace(/icon=\{<Icon as=\{(Fi\w+)\}/g, 'icon={<Icon as={$1 as ElementType}');
    
    // Pattern 3: leftIcon={<Icon as={FiIcon}
    content = content.replace(/leftIcon=\{<Icon as=\{(Fi\w+)\}/g, 'leftIcon={<Icon as={$1 as ElementType}');
    
    // Sauvegarder le fichier
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`✅ Fixed ${file}`);
  } else {
    console.log(`❌ File not found: ${file}`);
  }
});

console.log('\n✨ All files have been processed!'); 