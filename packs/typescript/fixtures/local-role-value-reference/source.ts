function execute(input: string) {
  const copy = input;
  const fn = execute;
  fn(copy);
  return input.length;
}

class Worker {
  run() {
    return 1;
  }
}

const WorkerRef = Worker;
const worker = new Worker();
const methodRef = worker.run;
worker.run();
