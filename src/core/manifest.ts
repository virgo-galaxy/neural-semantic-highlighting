export interface DocumentKindManifest {
  id: string;
  extensions: readonly string[];
}

export interface PackManifest {
  id: string;
  documentKinds: readonly DocumentKindManifest[];
}
