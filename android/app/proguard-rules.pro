# ProGuard rules for EchoHire
# Keep Firebase and Flutter entry points safe by default.

# Flutter
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugins.** { *; }
-keep class io.flutter.embedding.** { *; }

# Firebase (common keep rules)
-keepattributes *Annotation*
-keep class com.google.firebase.** { *; }
-dontwarn com.google.firebase.**

# OkHttp/Okio/HTTP (if used indirectly)
-dontwarn okhttp3.**
-dontwarn okio.**

# Keep models used by JSON (Dart side handles most JSON; safe minimal set)
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}
