import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_constants.dart';
class AppColors {
  static const Color primary = Color(0xFF0F766E);
  static const Color darkTeal = Color(0xFF0B4F4A);
  static const Color darkTeal2 = Color(0xFF0B5D55);
  static const Color textMain = Color(0xFF0F2E2B);
  static const Color textSecondary = Color(0xFF4B5F5C);
  static const Color textMuted = Color(0xFF7C918E);
  static const Color border = Color(0xFFDCE5E3);
  static const Color softSurface = Color(0xFFF3F7F6);
  static const Color lightTeal = Color(0xFFDDF1EE);
  static const Color background = Color(0xFFFAF9F5);
  static const Color surface = Colors.white;

  // Status pills
  static const Color takenBg = Color(0xFFD3EFE9);
  static const Color takenText = Color(0xFF0B5D55);
  static const Color dueBg = Color(0xFFFDEBC8);
  static const Color dueText = Color(0xFF7A3E05);
  static const Color dueAccent = Color(0xFFE9A23B);
  static const Color upcomingBg = Color(0xFFE6ECEB);
  static const Color upcomingText = Color(0xFF4B5F5C);
  static const Color missedBg = Color(0xFFFCE3E1);
  static const Color missedText = Color(0xFF9B1C1C);
}

class AppDarkColors {
  static const Color primary = Color(0xFF2DB3A6);
  static const Color textMain = Color(0xFFE6F2F0);
  static const Color textSecondary = Color(0xFFA9BDBA);
  static const Color textMuted = Color(0xFF7C918E);
  static const Color border = Color(0xFF2A3F3C);
  static const Color softSurface = Color(0xFF1B2D2B);
  static const Color lightTeal = Color(0xFF14423D);
  static const Color background = Color(0xFF0C1514);
  static const Color surface = Color(0xFF142120);

  // Status pills
  static const Color takenBg = Color(0xFF14423D);
  static const Color takenText = Color(0xFF8FE0D4);
  static const Color dueBg = Color(0xFF4A3410);
  static const Color dueText = Color(0xFFF5C77E);
  static const Color upcomingBg = Color(0xFF24312F);
  static const Color upcomingText = Color(0xFFA9BDBA);
  static const Color missedBg = Color(0xFF4A1F1D);
  static const Color missedText = Color(0xFFF2A3A0);
}

class AppTheme {
  static ThemeData get light {
    const scheme = ColorScheme(
      brightness: Brightness.light,
      primary: AppColors.primary,
      onPrimary: Colors.white,
      secondary: AppColors.darkTeal,
      onSecondary: Colors.white,
      error: AppColors.missedText,
      onError: Colors.white,
      surface: AppColors.surface,
      onSurface: AppColors.textMain,
    );
    return _buildTheme(
      scheme: scheme,
      background: AppColors.background,
      softSurface: AppColors.softSurface,
      border: AppColors.border,
      textMain: AppColors.textMain,
      textMuted: AppColors.textMuted,
      indicator: AppColors.lightTeal,
    );
  }

  static ThemeData get dark {
    const scheme = ColorScheme(
      brightness: Brightness.dark,
      primary: AppDarkColors.primary,
      onPrimary: Color(0xFF062B28),
      secondary: AppDarkColors.primary,
      onSecondary: Color(0xFF062B28),
      error: AppDarkColors.missedText,
      onError: Color(0xFF3A0E0C),
      surface: AppDarkColors.surface,
      onSurface: AppDarkColors.textMain,
    );
    return _buildTheme(
      scheme: scheme,
      background: AppDarkColors.background,
      softSurface: AppDarkColors.softSurface,
      border: AppDarkColors.border,
      textMain: AppDarkColors.textMain,
      textMuted: AppDarkColors.textMuted,
      indicator: AppDarkColors.lightTeal,
    );
  }

  static OutlineInputBorder _inputBorder(Color color) {
    return OutlineInputBorder(
      borderRadius: BorderRadius.circular(AppSizes.radiusButton),
      borderSide: BorderSide(color: color),
    );
  }

  static ThemeData _buildTheme({
    required ColorScheme scheme,
    required Color background,
    required Color softSurface,
    required Color border,
    required Color textMain,
    required Color textMuted,
    required Color indicator,
  }) {
    final textTheme = GoogleFonts.interTextTheme().apply(
      bodyColor: textMain,
      displayColor: textMain,
    );

    final buttonShape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(AppSizes.radiusButton),
    );

    final buttonTextStyle = GoogleFonts.inter(
      fontSize: 16,
      fontWeight: FontWeight.w600,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: background,
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: background,
        foregroundColor: textMain,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: textTheme.titleLarge,
      ),
      cardTheme: CardThemeData(
        color: scheme.surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSizes.radiusCard),
          side: BorderSide(color: border),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          minimumSize: const Size.fromHeight(AppSizes.buttonHeight),
          shape: buttonShape,
          textStyle: buttonTextStyle,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: scheme.primary,
          minimumSize: const Size.fromHeight(AppSizes.buttonHeight),
          shape: buttonShape,
          side: BorderSide(color: border),
          textStyle: buttonTextStyle,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: softSurface,
        hintStyle: TextStyle(color: textMuted),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 16,
        ),
        border: _inputBorder(border),
        enabledBorder: _inputBorder(border),
        focusedBorder: _inputBorder(scheme.primary),
        errorBorder: _inputBorder(scheme.error),
        focusedErrorBorder: _inputBorder(scheme.error),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: scheme.surface,
        indicatorColor: indicator,
        elevation: 0,
      ),
      dividerTheme: DividerThemeData(color: border, thickness: 1),
    );
  }
}