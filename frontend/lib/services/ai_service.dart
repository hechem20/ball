import 'dart:async';
import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../models/training.dart';

class AIServiceException implements Exception {
  final String message;

  AIServiceException(this.message);

  @override
  String toString() => message;
}

class AIService {
  final String baseUrl;
  final http.Client _client;

  AIService({
    String? baseUrl,
    http.Client? client,
  })  : baseUrl = baseUrl ?? _defaultBaseUrl(),
        _client = client ?? http.Client();

  static String _defaultBaseUrl() {
    if (kIsWeb) {
      return "http://127.0.0.1:5000";
    }

    return "http://10.0.2.2:8000";
  }

 Future<Map<String,dynamic>> analyzeTraining(
    TrainingType type,
    PlatformFile file,
) async {

    final request = http.MultipartRequest(
      "POST",
      Uri.parse("$baseUrl/api/training/analyze"),
    );

    request.fields["type"] = _typeToString(type);

    request.files.add(
      http.MultipartFile.fromBytes(
        "video",
        file.bytes!,
        filename: file.name,
      ),
    );

    final streamed = await _client.send(request);

    final response = await http.Response.fromStream(streamed);

    final json = jsonDecode(response.body);

    if(response.statusCode!=200){
        throw AIServiceException(json["error"]);
    }

    return Map<String,dynamic>.from(json["result"]);
}
  /// ===============================================================
  /// Upload vidéo
  /// ===============================================================
  Future<String> _submitJob(
    TrainingType type,
    PlatformFile videoFile,
  ) async {
    final request = http.MultipartRequest(
      "POST",
      Uri.parse("$baseUrl/api/training/analyze"),
    );

    request.fields["type"] = _typeToString(type);

    if (videoFile.bytes == null) {
      throw AIServiceException(
        "Impossible de lire la vidéo sélectionnée.",
      );
    }

    request.files.add(
      http.MultipartFile.fromBytes(
        "video",
        videoFile.bytes!,
        filename: videoFile.name,
      ),
    );

    late http.StreamedResponse streamed;

    try {
      streamed = await _client.send(request);
    } catch (e) {
      throw AIServiceException(
        "Impossible de contacter le serveur IA.\n$e",
      );
    }

    final response = await http.Response.fromStream(streamed);

    if (response.statusCode != 200) {
      throw AIServiceException(
        "Erreur ${response.statusCode}\n${response.body}",
      );
    }

    final json = jsonDecode(response.body);

    if (json["job_id"] == null) {
      throw AIServiceException("job_id absent.");
    }

    return json["job_id"];
  }

  /// ===============================================================
  /// Polling
  /// ===============================================================
  Future<Map<String, dynamic>> _pollUntilDone(
    String jobId, {
    required Duration pollInterval,
    required Duration timeout,
  }) async {
    final deadline = DateTime.now().add(timeout);

    while (DateTime.now().isBefore(deadline)) {
      final response = await _client.get(
        Uri.parse("$baseUrl/api/training/analyze/$jobId"),
      );

      if (response.statusCode != 200) {
        throw AIServiceException(
          "Erreur serveur ${response.statusCode}",
        );
      }

      final json = jsonDecode(response.body);

      final status = json["status"];

      if (status == "processing") {
        await Future.delayed(pollInterval);
        continue;
      }

      if (status == "done") {
        return Map<String, dynamic>.from(json["result"]);
      }

      if (status == "error") {
        throw AIServiceException(
          json["error"] ?? "Erreur IA",
        );
      }

      await Future.delayed(pollInterval);
    }

    throw AIServiceException(
      "Timeout : analyse trop longue.",
    );
  }

  String _typeToString(TrainingType type) {
    switch (type) {
      case TrainingType.speed:
        return "speed";

      case TrainingType.controlBall:
        return "control";

      case TrainingType.pass:
        return "pass";

      case TrainingType.shoot:
        return "shoot";
    }
  }

  void dispose() {
    _client.close();
  }
}