const profile = {
  id: "usr_42",
  name: "Ada",
  roles: ["admin", "editor"],
};

const greeting = `Hello, ${profile.name}!`;
const isAdmin = profile.roles.includes("admin");

console.log(greeting, { isAdmin });
