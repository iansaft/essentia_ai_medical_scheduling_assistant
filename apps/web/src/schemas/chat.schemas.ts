import { z } from "zod";

const chatAudioSchema = z.object({
  mimeType: z.string().min(1),
  base64: z.string().min(1),
});

const directReplySchema = z.object({
  message: z.string().min(1),
  audio: chatAudioSchema.nullable().optional(),
});

const outputReplySchema = z.object({
  output: z.string().min(1),
  audio: chatAudioSchema.nullable().optional(),
});

const textReplySchema = z.object({
  text: z.string().min(1),
  audio: chatAudioSchema.nullable().optional(),
});

export const n8nReplySchema = z.union([
  directReplySchema,
  outputReplySchema,
  textReplySchema,
  z
    .array(z.union([directReplySchema, outputReplySchema, textReplySchema]))
    .min(1),
]);
