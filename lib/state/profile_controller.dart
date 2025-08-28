// Profile state management with Riverpod
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/user_profile.dart';
import '../services/api_client.dart';

class ProfileState {
  final UserProfile? profile;
  final bool isLoading;
  final String? error;

  ProfileState({
    this.profile,
    this.isLoading = false,
    this.error,
  });

  ProfileState copyWith({
    UserProfile? profile,
    bool? isLoading,
    String? error,
  }) {
    return ProfileState(
      profile: profile ?? this.profile,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class ProfileController extends StateNotifier<ProfileState> {
  final ApiClient _apiClient = ApiClient();

  ProfileController() : super(ProfileState());

  Future<void> loadProfile() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final profileData = await _apiClient.getProfile();
      final profile = UserProfile.fromJson(profileData);
      state = state.copyWith(profile: profile, isLoading: false);
    } catch (e) {
      state = state.copyWith(error: e.toString(), isLoading: false);
      // Don't throw the error, just set it in state so UI can handle it gracefully
    }
  }

  Future<void> updateProfile({
    String? displayName,
    String? headline,
    List<String>? skills,
    String? location,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final updates = <String, dynamic>{};
      if (displayName != null) updates['displayName'] = displayName;
      if (headline != null) updates['headline'] = headline;
      if (skills != null) updates['skills'] = skills;
      if (location != null) updates['location'] = location;

      final updatedData = await _apiClient.updateProfile(updates);
      final updatedProfile = UserProfile.fromJson(updatedData);
      state = state.copyWith(profile: updatedProfile, isLoading: false);
    } catch (e) {
      state = state.copyWith(error: e.toString(), isLoading: false);
    }
  }
}

final profileControllerProvider = StateNotifierProvider<ProfileController, ProfileState>((ref) {
  return ProfileController();
});
