import 'package:flutter/material.dart';
import 'package:medisafe/screens/themes/theme_check_view.dart';

import 'core/config/app_constants.dart';
import 'core/config/app_theme.dart';

class MedisafeApp extends StatelessWidget {
  const MedisafeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConstants.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      home: const ThemeCheckScreen(),
    );
  }
}