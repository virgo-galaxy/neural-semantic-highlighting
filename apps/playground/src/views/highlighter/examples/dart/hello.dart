class User {
  final String name;
  final int age;

  const User(this.name, {required this.age});

  String get greeting => 'Hello, $name!';
}

(String, int) describe(User user) => (user.name, user.age);

void main(List<String> arguments) {
  final user = User(arguments.firstOrNull ?? 'Ada', age: 28);
  final (name, age) = describe(user);

  print(user.greeting);
  print('$name is $age years old.');
}
