import type { HighlightResult, PackManifest, SemanticPack } from "@nsh/core";

const LOCAL_PREFIX = "/__nsh/local";

interface HighlightResponse {
  result?: HighlightResult;
  error?: {
    message: string;
  };
}

/**
 * Browser-side adapter for the app's local-process runtime.
 *
 * This adapter is intentionally app-specific. Public NSH consumers continue
 * to depend only on SemanticPack and do not depend on this transport.
 */
export async function createLocalSemanticPack(): Promise<SemanticPack> {
  const manifestResponse = await fetch(`${LOCAL_PREFIX}/manifest`);

  if (!manifestResponse.ok) {
    throw new Error(`Unable to load local pack manifest (${manifestResponse.status}).`);
  }

  const manifest = (await manifestResponse.json()) as PackManifest;

  return {
    manifest,

    async highlight(request) {
      const response = await fetch(`${LOCAL_PREFIX}/highlight`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });
      const payload = (await response.json()) as HighlightResponse;

      if (!response.ok) {
        throw new Error(
          payload.error?.message ?? `Local highlighting failed (${response.status}).`,
        );
      }

      if (!payload.result) {
        throw new Error("Local highlighting returned no result.");
      }

      return payload.result;
    },
  };
}
