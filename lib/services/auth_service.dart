// Firebase authentication service
import 'package:firebase_auth/firebase_auth.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;

  User? get currentUser => _auth.currentUser;

  Stream<User?> get authStateChanges => _auth.authStateChanges();

  Future<UserCredential> signInWithEmailAndPassword(
    String email,
    String password,
  ) async {
    return await _auth.signInWithEmailAndPassword(
      email: email,
      password: password,
    );
  }

  Future<UserCredential> createUserWithEmailAndPassword(
    String email,
    String password,
  ) async {
    return await _auth.createUserWithEmailAndPassword(
      email: email,
      password: password,
    );
  }

  Future<void> signOut() async {
    await _auth.signOut();
  }

  Future<String?> getIdToken() async {
    final user = _auth.currentUser;
    if (user == null) {
      print('🔐 No user logged in - cannot get ID token');
      return null;
    }

    try {
      final token = await user.getIdToken();
      print('🔐 Got ID token for user: ${user.email}');
      return token;
    } catch (e) {
      print('❌ Failed to get ID token: $e');
      return null;
    }
  }
}
