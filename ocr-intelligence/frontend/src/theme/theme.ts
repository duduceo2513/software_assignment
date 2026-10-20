import { createTheme, type MantineColorsTuple } from "@mantine/core";

// Burgundy accent on white, near-black actions - flat, minimal
const brand: MantineColorsTuple = [
  "#fbeef1",
  "#f5d9e0",
  "#ecb2c0",
  "#e18a9f",
  "#d76683",
  "#cc4d6e",
  "#b02a4f",
  "#a01f45",
  "#8c1a3c",
  "#741431",
];

const FONT = 'Inter, "Segoe UI Variable", "Segoe UI", system-ui, -apple-system, Roboto, sans-serif';

export const theme = createTheme({
  primaryColor: "brand",
  primaryShade: 7,
  colors: { brand },
  black: "#111111",
  fontFamily: FONT,
  fontFamilyMonospace: '"JetBrains Mono", "Cascadia Code", Consolas, monospace',
  headings: { fontFamily: FONT, fontWeight: "700" },
  defaultRadius: "sm",
  radius: { xs: "2px", sm: "4px", md: "4px", lg: "6px", xl: "8px" },
  shadows: { xs: "none", sm: "none", md: "0 6px 20px rgba(0, 0, 0, 0.06)" },
  components: {
    Button: {
      defaultProps: { color: "dark.9", radius: "sm" },
      styles: { root: { fontWeight: 600 } },
    },
    Paper: { defaultProps: { radius: "sm" } },
    Badge: { defaultProps: { radius: "sm" }, styles: { root: { fontWeight: 600, textTransform: "none", letterSpacing: 0 } } },
    SegmentedControl: { defaultProps: { radius: "sm", color: "dark.9" } },
    Progress: { defaultProps: { radius: "xs", size: "sm" } },
  },
});
