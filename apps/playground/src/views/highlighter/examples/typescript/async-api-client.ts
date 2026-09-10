interface User {
  id: number;
  name: string;
  email?: string;
  roles: readonly string[];
  createdAt: Date;
}

type ApiResult<T> = { success: true; data: T } | { success: false; error: string };

class UserService {
  private readonly users = new Map<number, User>();

  constructor(private readonly apiBaseUrl: string) {}

  async fetchUser(id: number): Promise<ApiResult<User>> {
    const url = `${this.apiBaseUrl}/users/${id}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        return {
          success: false,
          error: `Request failed with status ${response.status}`,
        };
      }

      const user = (await response.json()) as User;
      this.users.set(user.id, user);

      return { success: true, data: user };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  findByEmail(email: string): User | undefined {
    const normalized = email.trim().toLowerCase();
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/i;

    if (!emailPattern.test(normalized)) {
      return undefined;
    }

    return [...this.users.values()].find((user) => user.email?.toLowerCase() === normalized);
  }
}

void new UserService("https://api.example.com").fetchUser(42);
