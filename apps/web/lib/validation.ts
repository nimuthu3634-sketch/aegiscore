import { z } from "zod";

import type { Integration } from "@/types/domain";

export const passwordPolicyHint = "Use at least 8 characters with uppercase, lowercase, number, and symbol characters.";
export const maxUploadBytes = 5 * 1024 * 1024;

export function strongPasswordSchema(label = "Password") {
  return z
    .string()
    .min(8, `${label} must be at least 8 characters.`)
    .max(128, `${label} must be 128 characters or fewer.`)
    .refine((value) => /[a-z]/.test(value), `${label} must include a lowercase letter.`)
    .refine((value) => /[A-Z]/.test(value), `${label} must include an uppercase letter.`)
    .refine((value) => /\d/.test(value), `${label} must include a number.`)
    .refine((value) => /[^A-Za-z0-9]/.test(value), `${label} must include a symbol.`);
}

export function validateImportFile(file: File, integration?: Integration) {
  if (file.size <= 0) {
    throw new Error("Uploaded file was empty.");
  }
  if (file.size > maxUploadBytes) {
    throw new Error("Uploaded file exceeded the 5 MB limit.");
  }
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  const allowedFormats = integration?.supported_formats ?? ["json"];
  if (!allowedFormats.includes(extension)) {
    throw new Error(`Unsupported file type. Allowed formats: ${allowedFormats.map((item) => `.${item}`).join(", ")}`);
  }
}
