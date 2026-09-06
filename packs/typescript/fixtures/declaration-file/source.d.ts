export interface User {
  readonly id: string;
  name?: string;
}

export declare function createUser(name: string): User;
export declare const VERSION: string;
