sealed class Result {}

final class Success extends Result {
  final String name;
  final int count;
  Success(this.name, this.count);
}

final class Failure extends Result {
  final String reason;
  Failure(this.reason);
}

String describe(Result result) => switch (result) {
  Success(:final name, :final count) when count > 0 => '$name: $count',
  Success() => 'Empty',
  Failure(:final reason) => 'Failed: $reason',
};

void main() {
  final (:name, :count) = (name: 'Documents', count: 3);
  final values = <Object>[1, 'two'];
  if (values case [int first, String second]) {
    print('$first / $second');
  }
  print(describe(Success(name, count)));
}
