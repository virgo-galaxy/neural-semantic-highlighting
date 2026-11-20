import 'package:flutter/material.dart';

class NameForm extends StatefulWidget {
  const NameForm({super.key});
  @override
  State<NameForm> createState() => _NameFormState();
}

class _NameFormState extends State<NameForm> {
  final formKey = GlobalKey<FormState>();
  final controller = TextEditingController();

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  void submit() {
    if (!(formKey.currentState?.validate() ?? false)) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Saved: ${controller.text}')),
    );
  }

  @override
  Widget build(BuildContext context) => Form(
    key: formKey,
    child: Column(children: [
      TextFormField(
        controller: controller,
        decoration: const InputDecoration(labelText: 'Document name'),
        validator: (value) =>
            value == null || value.trim().isEmpty ? 'Enter a name' : null,
      ),
      FilledButton(onPressed: submit, child: const Text('Save')),
    ]),
  );
}
