export type ContentCategory = "code" | "formats";

/** Display/input metadata only: never imports a model or inference runtime. */
export interface ContentType {
  readonly id: string;
  readonly label: string;
  readonly category: ContentCategory;
  readonly aliases: readonly string[];
  readonly modelId: string;
  readonly extensions: readonly string[];
  readonly iconId: string;
  /** Named framework profile, e.g. Flutter, handled as its underlying source kind. */
  readonly documentKind?: string;
  readonly frameworks?: readonly string[];
  readonly modelDependencies?: readonly string[];
  /** Filename variants stay internal rather than becoming separate menu entries. */
  readonly fileVariants?: readonly {
    readonly id: string;
    readonly extensions: readonly string[];
  }[];
}
