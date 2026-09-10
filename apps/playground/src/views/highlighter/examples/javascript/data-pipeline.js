const normalizeEmail = (value) => value.trim().toLowerCase();
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/i;

function* validUsers(users) {
  for (const user of users) {
    const email = normalizeEmail(user.email ?? "");

    if (emailPattern.test(email)) {
      yield { ...user, email };
    }
  }
}

const users = [
  { id: 1, name: "Ada", email: "ADA@example.com" },
  { id: 2, name: "Linus", email: "invalid" },
  { id: 3, name: "Grace", email: "grace@example.org" },
];

const domains = [...validUsers(users)]
  .map(({ email }) => email.split("@")[1])
  .filter(Boolean)
  .reduce((counts, domain) => {
    counts[domain] = (counts[domain] ?? 0) + 1;
    return counts;
  }, {});

console.log(domains);
