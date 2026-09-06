class User {
  readonly name: string;

  constructor(name: string) {
    this.name = name;
  }

  static async load(): Promise<User> {
    return new User("value");
  }
}
