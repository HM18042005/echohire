// User profile data model
class UserProfile {
  final String uid;
  final String email;
  final String displayName;
  final String headline;
  final List<String> skills;
  final String location;
  final String createdAt;
  final String updatedAt;

  UserProfile({
    required this.uid,
    required this.email,
    required this.displayName,
    required this.headline,
    required this.skills,
    required this.location,
    required this.createdAt,
    required this.updatedAt,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      uid: json['uid'] ?? '',
      email: json['email'] ?? '',
      displayName: json['displayName'] ?? '',
      headline: json['headline'] ?? '',
      skills: List<String>.from(json['skills'] ?? []),
      location: json['location'] ?? '',
      createdAt: json['createdAt'] ?? '',
      updatedAt: json['updatedAt'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'uid': uid,
      'email': email,
      'displayName': displayName,
      'headline': headline,
      'skills': skills,
      'location': location,
      'createdAt': createdAt,
      'updatedAt': updatedAt,
    };
  }

  UserProfile copyWith({
    String? displayName,
    String? headline,
    List<String>? skills,
    String? location,
  }) {
    return UserProfile(
      uid: uid,
      email: email,
      displayName: displayName ?? this.displayName,
      headline: headline ?? this.headline,
      skills: skills ?? this.skills,
      location: location ?? this.location,
      createdAt: createdAt,
      updatedAt: updatedAt,
    );
  }
}
