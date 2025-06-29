# Guide de Style Mode Clair - ESAG GED

Ce document contient tous les éléments de style utilisés dans la page **SharedDocuments.tsx** pour implémenter un design moderne et cohérent en mode clair dans toute l'application.

## 🎨 Palette de Couleurs Mode Clair

### Couleurs Principales

```typescript
// Couleurs adaptatives avec useColorModeValue
const bgColor = useColorModeValue("gray.50", "gray.900"); // Arrière-plan principal
const cardBg = useColorModeValue("white", "gray.800"); // Arrière-plan des cartes
const borderColor = useColorModeValue("gray.200", "gray.600"); // Bordures
const textColor = useColorModeValue("gray.800", "white"); // Texte principal
const mutedColor = useColorModeValue("gray.600", "gray.400"); // Texte secondaire
const inputBg = useColorModeValue("white", "gray.700"); // Arrière-plan inputs
```

### Couleurs Spécifiques Mode Clair

- **Arrière-plan principal** : `gray.50` (très léger)
- **Cartes/Conteneurs** : `white` (blanc pur)
- **Bordures** : `gray.200` (gris très clair)
- **Texte principal** : `gray.800` (gris foncé)
- **Texte secondaire** : `gray.600` (gris moyen)
- **Inputs** : `white` (blanc pur)

## 🏗️ Structure Layout

### Container Principal

```tsx
<Box minHeight="100vh" bg={bgColor}>
  <Container maxW="container.xl" py={8}>
    {/* Contenu */}
  </Container>
</Box>
```

### Espacement Standard

- **Container padding** : `py={8}` (32px vertical)
- **Sections spacing** : `mb={8}` (32px entre sections)
- **Elements spacing** : `spacing={6}` ou `spacing={4}`

## 📋 Composants de Base

### En-tête de Page

```tsx
<VStack spacing={6} mb={8}>
  <HStack spacing={4}>
    <CustomIcon type="share" size="lg" />
    <VStack align="start" spacing={1}>
      <Heading size="xl" color={textColor}>
        Titre Principal
      </Heading>
      <Text color={mutedColor} fontSize="lg">
        Description/sous-titre
      </Text>
    </VStack>
  </HStack>
</VStack>
```

### Card Standard

```tsx
<Card
  bg={cardBg}
  borderColor={borderColor}
  shadow="lg"
  _hover={{
    shadow: "xl",
    transform: "translateY(-2px)",
    borderColor: "blue.300",
  }}
  transition="all 0.2s"
>
  <CardBody p={6}>{/* Contenu */}</CardBody>
</Card>
```

## 🔍 Section Filtres

### Container Filtres

```tsx
<Card mb={8} bg={cardBg} borderColor={borderColor} shadow="lg">
  <CardHeader>
    <HStack spacing={2}>
      <CustomIcon type="search" size="md" />
      <Heading size="md" color={textColor}>
        Filtres de recherche
      </Heading>
    </HStack>
  </CardHeader>
  <CardBody pt={0}>
    <Grid
      templateColumns="repeat(auto-fit, minmax(250px, 1fr))"
      gap={6}
      alignItems="end"
    >
      {/* Items */}
    </Grid>
  </CardBody>
</Card>
```

### Input Standard

```tsx
<Input
  placeholder="Texte placeholder..."
  size="lg"
  bg={inputBg}
  borderColor={borderColor}
  _focus={{ borderColor: "blue.500", boxShadow: "0 0 0 1px blue.500" }}
/>
```

### Select Standard

```tsx
<Select size="lg" bg={inputBg} borderColor={borderColor}>
  <option value="">Option par défaut</option>
  <option value="value">🔥 Option avec emoji</option>
</Select>
```

## 🏷️ Tags et Badges

### Badge de Résultats

```tsx
<Badge colorScheme="blue" fontSize="md" px={3} py={1} borderRadius="full">
  {count} résultat(s)
</Badge>
```

### Tags Permissions (colorés)

```tsx
const permissionLabels = {
  lecture: { label: "Lecture", color: "blue" },
  téléchargement: { label: "Téléchargement", color: "green" },
  modification: { label: "Modification", color: "orange" },
  commentaire: { label: "Commentaire", color: "purple" },
  partage_supplementaire: { label: "Re-partage", color: "pink" },
};

<Tag size="sm" variant="solid" colorScheme={config.color} mr={1} mb={1}>
  <TagLabel>{config.label}</TagLabel>
</Tag>;
```

### Badge Type Destinataire

```tsx
<Badge
  colorScheme={typeConfig.color}
  variant="solid"
  fontSize="xs"
  px={2}
  py={1}
  borderRadius="full"
>
  {typeConfig.icon} {typeConfig.label}
</Badge>
```

## 🚨 Alertes et États

### Alert Standard

```tsx
<Alert
  status="error" // ou "warning", "success", "info"
  borderRadius="lg"
  p={6}
  variant="left-accent"
>
  <AlertIcon boxSize="24px" />
  <VStack align="start" spacing={2}>
    <Text fontSize="lg" fontWeight="bold">
      Titre de l'erreur
    </Text>
    <Text>Description détaillée</Text>
  </VStack>
</Alert>
```

### État de Chargement

```tsx
<Box
  minHeight="100vh"
  bg={bgColor}
  display="flex"
  justifyContent="center"
  alignItems="center"
>
  <VStack spacing={4}>
    <Spinner size="xl" color="blue.500" thickness="4px" />
    <Text fontSize="lg" color={mutedColor}>
      Message de chargement...
    </Text>
  </VStack>
</Box>
```

### État Vide

```tsx
<Card bg={cardBg} borderColor={borderColor} shadow="lg">
  <CardBody textAlign="center" py={16}>
    <VStack spacing={6}>
      <CustomIcon type="share" size="lg" />
      <VStack spacing={2}>
        <Heading size="lg" color={mutedColor}>
          Titre état vide
        </Heading>
        <Text color={mutedColor} fontSize="lg">
          Description explicative
        </Text>
      </VStack>
    </VStack>
  </CardBody>
</Card>
```

## 🔘 Boutons et Actions

### Bouton Principal

```tsx
<Button
  size="sm"
  variant="solid"
  colorScheme="blue"
  leftIcon={<CustomIcon type="view" />}
>
  Action Principale
</Button>
```

### Bouton Secondaire

```tsx
<Button
  size="sm"
  variant="outline"
  colorScheme="green"
  leftIcon={<CustomIcon type="download" />}
>
  Action Secondaire
</Button>
```

### Bouton Ghost/Subtil

```tsx
<Button size="sm" variant="ghost" colorScheme="gray">
  Action Discrète
</Button>
```

### Menu Contextuel

```tsx
<Menu>
  <MenuButton
    as={IconButton}
    aria-label="Plus d'options"
    size="sm"
    variant="ghost"
    colorScheme="gray"
  >
    <CustomIcon type="menu" />
  </MenuButton>
  <MenuList>
    <MenuItem>
      <HStack spacing={3}>
        <CustomIcon type="view" />
        <Text>Action menu</Text>
      </HStack>
    </MenuItem>
  </MenuList>
</Menu>
```

## 🎯 Grid et Layout

### Grid Responsive

```tsx
<Grid templateColumns="repeat(auto-fill, minmax(400px, 1fr))" gap={8}>
  {/* Items */}
</Grid>
```

### Grid Filtres

```tsx
<Grid
  templateColumns="repeat(auto-fit, minmax(250px, 1fr))"
  gap={6}
  alignItems="end"
>
  <GridItem>
    <VStack align="start" spacing={2}>
      <Text fontSize="sm" fontWeight="semibold" color={textColor}>
        Label
      </Text>
      {/* Input/Select */}
    </VStack>
  </GridItem>
</Grid>
```

## 🖼️ Icônes avec Emojis

### Composant CustomIcon

```tsx
const CustomIcon: React.FC<{ type: string; size?: "sm" | "md" | "lg" }> = ({
  type,
  size = "sm",
}) => {
  let fontSize = "16px";
  if (size === "md") fontSize = "24px";
  if (size === "lg") fontSize = "40px";

  const iconStyle = {
    fontSize,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
  };

  const icons = {
    utilisateur: "👤",
    role: "👥",
    organisation: "🏢",
    view: "👁️",
    download: "⬇️",
    edit: "✏️",
    comment: "💬",
    delete: "🗑️",
    search: "🔍",
    schedule: "📅",
    warning: "⚠️",
    share: "📤",
    menu: "⋮",
  };

  return <span style={iconStyle}>{icons[type] || "📄"}</span>;
};
```

## 📱 Responsive Design

### Breakpoints Utilisés

- **Container** : `maxW="container.xl"` (1200px max)
- **Cards minimum** : `minmax(400px, 1fr)`
- **Filtres minimum** : `minmax(250px, 1fr)`

### Espacement Responsive

```tsx
// Mobile-first approach
<VStack spacing={{ base: 4, md: 6 }}>
<Grid gap={{ base: 4, md: 6, lg: 8 }}>
<Container maxW={{ base: "container.md", lg: "container.xl" }}>
```

## 🎨 Effets Visuels

### Hover Effects

```tsx
_hover={{
  shadow: 'xl',
  transform: 'translateY(-2px)',
  borderColor: 'blue.300'
}}
transition="all 0.2s"
```

### Focus States

```tsx
_focus={{
  borderColor: 'blue.500',
  boxShadow: '0 0 0 1px blue.500'
}}
```

### Shadows

- **Card standard** : `shadow="lg"`
- **Card hover** : `shadow="xl"`

## 📋 Typographie

### Tailles de Texte

- **Heading XL** : `size="xl"` (titre principal)
- **Heading MD** : `size="md"` (sous-titres)
- **Text LG** : `fontSize="lg"` (descriptions importantes)
- **Text SM** : `fontSize="sm"` (texte secondaire)
- **Text XS** : `fontSize="xs"` (détails)

### Poids de Police

- **Bold** : `fontWeight="bold"`
- **Semibold** : `fontWeight="semibold"`
- **Medium** : `fontWeight="medium"`

## 🔧 Utilitaires

### Truncation

```tsx
<Text noOfLines={2}>Texte qui peut être tronqué</Text>
<Heading noOfLines={2} title={fullText}>Titre tronqué avec tooltip</Heading>
```

### Spacing Utilities

```tsx
<Spacer />  // Pousse les éléments aux extrémités
<Divider borderColor={borderColor} />  // Séparateur
```

## 📦 Imports Nécessaires

```tsx
import {
  Box,
  VStack,
  HStack,
  Text,
  Heading,
  Input,
  Select,
  Button,
  Card,
  CardBody,
  CardHeader,
  Badge,
  Tag,
  TagLabel,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Alert,
  AlertIcon,
  Spinner,
  Tooltip,
  Grid,
  GridItem,
  Flex,
  Spacer,
  Divider,
  useToast,
  useColorModeValue,
  Container,
} from "@chakra-ui/react";
```

---

## 🎯 Application dans d'Autres Composants

Pour appliquer ce style dans d'autres composants :

1. **Importer les hooks** : `useColorModeValue`
2. **Définir les couleurs** au début du composant
3. **Utiliser la structure** Container > Card > CardBody
4. **Appliquer les espacements** standards (py={8}, mb={8}, spacing={6})
5. **Utiliser CustomIcon** au lieu d'icônes Material-UI
6. **Respecter la hiérarchie** typographique
7. **Ajouter les effets** hover et focus states

Ce guide garantit une cohérence visuelle parfaite dans toute l'application ESAG GED en mode clair.
