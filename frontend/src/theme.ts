import { extendTheme } from "@chakra-ui/react";

// Définition du thème personnalisé
const theme = extendTheme({
  colors: {
    brand: {
      50: "#e6f0ff",
      100: "#b3d1ff",
      200: "#80b3ff",
      300: "#4d94ff",
      400: "#1a75ff",
      500: "#0066ff", // Couleur principale
      600: "#0052cc",
      700: "#003d99",
      800: "#002966",
      900: "#001433",
    },
    background: {
      primary: "#141829",
      secondary: "#1c2338",
      tertiary: "#2a3657",
    },
  },
  fonts: {
    heading: "'Inter', sans-serif",
    body: "'Inter', sans-serif",
  },
  styles: {
    global: {
      body: {
        bg: "#141829",
        color: "white",
      },
      // Améliorer la visibilité du texte et des composants
      "h1, h2, h3, h4, h5, h6": {
        color: "white",
        fontWeight: "600",
      },
      "p, span, label, div": {
        color: "white",
      },
      // Améliorer le contraste des tableaux
      "table": {
        bg: "#2a3657",
        color: "white",
      },
      "th": {
        bg: "#1c2338",
        color: "white !important",
        fontWeight: "600",
      },
      "td": {
        borderColor: "#3a445e !important",
      },
      "tr:hover": {
        bg: "#374269 !important",
      },
    },
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: "600",
        borderRadius: "md",
      },
      variants: {
        primary: {
          bg: "brand.500",
          color: "white",
          _hover: {
            bg: "brand.600",
          },
        },
        secondary: {
          bg: "background.tertiary",
          color: "white",
          _hover: {
            bg: "background.secondary",
          },
        },
      },
    },
    Input: {
      baseStyle: {
        field: {
          bg: "#2a3657",
          color: "white",
          borderColor: "#3a445e",
          _hover: {
            borderColor: "brand.500",
          },
          _focus: {
            borderColor: "brand.500",
            boxShadow: "0 0 0 1px #0066ff",
          },
          _placeholder: {
            color: "gray.400",
          },
        },
      },
    },
    Select: {
      baseStyle: {
        field: {
          bg: "#2a3657",
          color: "white",
          borderColor: "#3a445e",
          _hover: {
            borderColor: "brand.500",
          },
          _focus: {
            borderColor: "brand.500",
            boxShadow: "0 0 0 1px #0066ff",
          },
        },
      },
    },
    Menu: {
      baseStyle: {
        list: {
          bg: "#1c2338",
          borderColor: "#3a445e",
          border: "1px solid",
          borderRadius: "md",
          boxShadow: "0 8px 16px rgba(0, 0, 0, 0.4)",
          zIndex: 1500,
          minW: "150px",
        },
        item: {
          bg: "transparent",
          color: "white",
          _hover: {
            bg: "#2d3250",
            color: "white",
          },
          _focus: {
            bg: "#2d3250",
            color: "white",
          },
        },
      },
    },
    Table: {
      baseStyle: {
        th: {
          color: "white",
        },
        td: {
          color: "white",
        },
      },
    },
  },
});

export { theme };