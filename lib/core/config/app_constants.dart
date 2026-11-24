class AppConstants {
  static const String appName = 'Medisafe';
  static const String baseUrl = 'https://medisafe-app-nh82.vercel.app';

  // Free hosting can be slow on the first request
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration sendTimeout = Duration(seconds: 30);
}

class AppSizes {
  static const double radiusCard = 20;
  static const double radiusButton = 16;
  static const double radiusHeader = 32;
  static const double radiusPill = 999;

  static const double buttonHeight = 52;

  static const double paddingScreen = 20;
  static const double spacingSmall = 8;
  static const double spacingMedium = 16;
  static const double spacingLarge = 24;
}