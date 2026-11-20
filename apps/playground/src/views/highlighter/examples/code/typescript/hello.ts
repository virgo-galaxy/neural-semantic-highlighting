interface UserProfile {
  id: string;
  name: string;
  roles: readonly string[];
}

const profile: UserProfile = {
  id: "usr_42",
  name: "Ada",
  roles: ["admin", "editor"],
};

const greeting = `Hello, ${profile.name}!`;
console.log(greeting, profile.roles.includes("admin"));
