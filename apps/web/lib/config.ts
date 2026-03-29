import { brandName, brandPalette } from "@aegiscore/config";

export const appConfig = {
  appName: brandName,
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  wsBaseUrl: process.env.NEXT_PUBLIC_WS_BASE_URL ?? "ws://localhost:8000/api/v1",
  brand: {
    orange: brandPalette.primaryOrange,
    black: brandPalette.primaryBlack,
    white: brandPalette.white,
    surface: brandPalette.surface,
    border: brandPalette.border,
  },
} as const;
