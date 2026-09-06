interface Repository<T extends Entity> {
  readonly id?: string;
  find(id: string): T;
}
