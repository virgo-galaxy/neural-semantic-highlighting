import type { HighlightResult } from "@nsh/core";

export interface ProviderResponse {
  id: number;
  result?: HighlightResult;
  error?: {
    message: string;
  };
}

export function parseProviderResponse(line: string): ProviderResponse {
  let value: unknown;

  try {
    value = JSON.parse(line);
  } catch {
    throw new Error("Local semantic provider wrote invalid JSON to stdout.");
  }

  if (!isRecord(value) || !Number.isInteger(value.id)) {
    throw new Error("Local semantic provider response must contain an integer id.");
  }

  const id = value.id as number;

  if (value.error !== undefined) {
    if (!isRecord(value.error) || typeof value.error.message !== "string") {
      throw new Error("Local semantic provider returned an invalid error response.");
    }

    return {
      id,
      error: { message: value.error.message },
    };
  }

  if (!isHighlightResult(value.result)) {
    throw new Error("Local semantic provider returned an invalid HighlightResult.");
  }

  return {
    id,
    result: value.result,
  };
}

export function asProtocolError(value: unknown): Error {
  return value instanceof Error ? value : new Error("Local semantic provider protocol error.");
}

function isHighlightResult(value: unknown): value is HighlightResult {
  return (
    isRecord(value) &&
    (value.offsetEncoding === "utf-8" ||
      value.offsetEncoding === "utf-16" ||
      value.offsetEncoding === "utf-32") &&
    Array.isArray(value.spans)
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
