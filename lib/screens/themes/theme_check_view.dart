import 'package:flutter/material.dart';
import '../../core/config/app_constants.dart';

// Temporary screen to check the theme. It will be removed in F3.
class ThemeCheckScreen extends StatelessWidget {
  const ThemeCheckScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text(AppConstants.appName)),
      body: Padding(
        padding: const EdgeInsets.all(AppSizes.paddingScreen),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(AppSizes.spacingMedium),
                child: Text(
                  'Never miss a dose.',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ),
            const SizedBox(height: AppSizes.spacingMedium),
            const TextField(
              decoration: InputDecoration(hintText: 'Email'),
            ),
            const SizedBox(height: AppSizes.spacingMedium),
            ElevatedButton(
              onPressed: () {},
              child: const Text('Log in'),
            ),
            const SizedBox(height: AppSizes.spacingSmall),
            OutlinedButton(
              onPressed: () {},
              child: const Text('Create account'),
            ),
          ],
        ),
      ),
    );
  }
}