"""
Enhanced Visual Intelligence Module (Agent 4)
Computer vision pipeline for real-time interview analytics.

Features:
  1. Eye contact tracking       — gaze direction estimation via head pose
  2. Facial expression analysis — blendshape-aware expression classification
  3. Posture analysis           — shoulder symmetry, forward head, torso angle
  4. Stress detection           — blink rate, brow furrow, lip press
  5. Engagement score           — composite of all dimensions
  6. Smile confidence           — blendshape-based smile intensity
  7. Head movement tracking     — yaw/pitch/roll velocity over time
  8. Attention score            — gaze + head orientation + blink pattern
  9. Nervous behavior detection — micro-expressions, lip biting, fidgeting

Uses MediaPipe FaceLandmarker (468 landmarks) + PoseLandmarker (33 landmarks).
Blendshapes enabled for expression classification.
Temporal state maintained via VisualIntelligenceEngine.
"""

import os
import math
import time
import logging
import numpy as np
from typing import Optional
from collections import deque

logger = logging.getLogger("visual_intel")

MODEL_DIR = os.path.join(os.path.dirname(__file__))
FACE_MODEL_PATH = os.path.join(MODEL_DIR, "face_landmarker.task")
POSE_MODEL_PATH = os.path.join(MODEL_DIR, "pose_landmarker.task")

try:
    from mediapipe.tasks.python.vision import (
        FaceLandmarker, FaceLandmarkerOptions,
        PoseLandmarker, PoseLandmarkerOptions,
        RunningMode,
    )
    from mediapipe.tasks.python.core.base_options import BaseOptions, Delegate
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


_face_landmarker = None
_pose_landmarker = None


def _get_face_landmarker():
    global _face_landmarker
    if _face_landmarker is None and MEDIAPIPE_AVAILABLE:
        if not os.path.exists(FACE_MODEL_PATH):
            return None
        try:
            with open(FACE_MODEL_PATH, "rb") as f:
                model_data = f.read()
            options = FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_buffer=model_data, delegate=Delegate.CPU),
                running_mode=RunningMode.IMAGE,
                output_face_blendshapes=True,
                output_facial_transformation_matrixes=True,
            )
            _face_landmarker = FaceLandmarker.create_from_options(options)
        except Exception as e:
            logger.error("Failed to load face_landmarker model: %s", e)
    return _face_landmarker


def _get_pose_landmarker():
    global _pose_landmarker
    if _pose_landmarker is None and MEDIAPIPE_AVAILABLE:
        if not os.path.exists(POSE_MODEL_PATH):
            return None
        try:
            with open(POSE_MODEL_PATH, "rb") as f:
                model_data = f.read()
            options = PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_buffer=model_data, delegate=Delegate.CPU),
                running_mode=RunningMode.IMAGE,
            )
            _pose_landmarker = PoseLandmarker.create_from_options(options)
        except Exception as e:
            logger.error("Failed to load pose_landmarker model: %s", e)
    return _pose_landmarker


def _decode_image(image_data: bytes) -> Optional[np.ndarray]:
    try:
        import cv2
        arr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception as e:
        logger.warning("Image decode failed: %s", e)
        return None


# ──────────────────────────────────────────────
# BLENDSHAPE INDICES (MediaPipe Face Landmarker)
# ──────────────────────────────────────────────

BLENDSHAPE = {
    "browDownLeft": 2, "browDownRight": 3,
    "browInnerUp": 4, "browOuterUpLeft": 5, "browOuterUpRight": 6,
    "cheekPuff": 7, "cheekSquintLeft": 8, "cheekSquintRight": 9,
    "eyeBlinkLeft": 10, "eyeBlinkRight": 11,
    "eyeLookDownLeft": 12, "eyeLookDownRight": 13,
    "eyeLookInLeft": 14, "eyeLookInRight": 15,
    "eyeLookOutLeft": 16, "eyeLookOutRight": 17,
    "eyeLookUpLeft": 18, "eyeLookUpRight": 19,
    "eyeSquintLeft": 20, "eyeSquintRight": 21,
    "eyeWideLeft": 22, "eyeWideRight": 23,
    "jawForward": 24, "jawLeft": 25, "jawOpen": 26, "jawRight": 27,
    "mouthClose": 28, "mouthDimpleLeft": 29, "mouthDimpleRight": 30,
    "mouthFrownLeft": 31, "mouthFrownRight": 32,
    "mouthFunnel": 33, "mouthLeft": 34, "mouthLowerDownLeft": 35,
    "mouthLowerDownRight": 36, "mouthPressLeft": 37, "mouthPressRight": 38,
    "mouthPucker": 39, "mouthRight": 40, "mouthRollLower": 41,
    "mouthRollUpper": 42, "mouthShrugLower": 43, "mouthShrugUpper": 44,
    "mouthSmileLeft": 45, "mouthSmileRight": 46,
    "mouthStretchLeft": 47, "mouthStretchRight": 48,
    "mouthUpperUpLeft": 49, "mouthUpperUpRight": 50,
    "noseSneerLeft": 51, "noseSneerRight": 52,
    "headNod": 53, "headRotate": 54,
}


# ──────────────────────────────────────────────
# STATE TRACKER
# ──────────────────────────────────────────────

class VisualIntelligenceEngine:
    """Stateful engine maintaining temporal history for movement/attention tracking."""

    def __init__(self, history_seconds: float = 10.0, frame_rate: float = 3.0):
        self.maxlen = int(history_seconds * frame_rate)
        self.history: deque = deque(maxlen=self.maxlen)
        self._last_head = None
        self._blink_counter = 0
        self._last_blink_state = (0.0, 0.0)

    def add_frame(self, result: dict):
        result["timestamp"] = time.time()
        self.history.append(result)

    def get_history(self, seconds: float = 5.0) -> list:
        now = time.time()
        return [r for r in self.history if now - r.get("timestamp", 0) <= seconds]

    def compute_blink_rate(self) -> float:
        recent = self.get_history(10.0)
        if len(recent) < 2:
            return 0.0
        total_blinks = sum(r.get("blink_detected", False) for r in recent)
        duration = recent[-1]["timestamp"] - recent[0]["timestamp"]
        if duration <= 0:
            return 0.0
        return total_blinks / duration * 60  # blinks per minute

    def compute_head_movement_velocity(self) -> dict:
        recent = self.get_history(3.0)
        if len(recent) < 4:
            return {"yaw_velocity": 0, "pitch_velocity": 0, "roll_velocity": 0, "overall": 0}
        yaws = [r.get("head_yaw", 0) for r in recent]
        pitches = [r.get("head_pitch", 0) for r in recent]
        rolls = [r.get("head_roll", 0) for r in recent]
        duration = recent[-1]["timestamp"] - recent[0]["timestamp"]
        if duration <= 0:
            return {"yaw_velocity": 0, "pitch_velocity": 0, "roll_velocity": 0, "overall": 0}
        def velocity(series):
            return abs(series[-1] - series[0]) / duration
        yv = velocity(yaws)
        pv = velocity(pitches)
        rv = velocity(rolls)
        return {
            "yaw_velocity": round(yv, 1),
            "pitch_velocity": round(pv, 1),
            "roll_velocity": round(rv, 1),
            "overall": round((yv + pv + rv) / 3, 1),
        }


_engine: Optional[VisualIntelligenceEngine] = None


def _get_engine() -> VisualIntelligenceEngine:
    global _engine
    if _engine is None:
        _engine = VisualIntelligenceEngine()
    return _engine


# ──────────────────────────────────────────────
# SINGLE FRAME ANALYSIS
# ──────────────────────────────────────────────

def analyze_frame(image_data: bytes) -> dict:
    """
    Analyze a single video frame and return all metrics.

    Returns dict with:
      face_detected, eye_contact_score, expression, expression_confidence,
      posture_score, stress_indicator, smile_score, head_yaw/pitch/roll,
      head_movement_velocity, attention_score, engagement_score,
      nervousness_indicator, blink_detected, blink_rate
    """
    result = _default_result()
    if not MEDIAPIPE_AVAILABLE:
        result["error"] = "MediaPipe not installed"
        return result

    img_rgb = _decode_image(image_data)
    if img_rgb is None:
        result["error"] = "Could not decode image"
        return result

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
    engine = _get_engine()

    # ── FACE ANALYSIS ──
    face_landmarker = _get_face_landmarker()
    if face_landmarker:
        try:
            face_result = face_landmarker.detect(mp_image)
            if face_result.face_landmarks:
                result["face_detected"] = True
                lm = face_result.face_landmarks[0]
                blendshapes = _extract_blendshapes(face_result)

                # Head pose from transformation matrix
                yaw, pitch, roll = 0.0, 0.0, 0.0
                if face_result.facial_transformation_matrixes:
                    yaw, pitch, roll = _extract_euler_angles(
                        face_result.facial_transformation_matrixes[0]
                    )
                result["head_yaw"] = round(math.degrees(yaw), 1)
                result["head_pitch"] = round(math.degrees(pitch), 1)
                result["head_roll"] = round(math.degrees(roll), 1)

                # ── 1. Eye Contact Score ──
                result["eye_contact_score"] = _compute_eye_contact(
                    yaw, pitch, roll, lm
                )

                # ── 2. Facial Expression ──
                expr_result = _classify_expression(blendshapes, lm)
                result["expression"] = expr_result["label"]
                result["expression_confidence"] = expr_result["confidence"]

                # ── 6. Smile Confidence ──
                result["smile_score"] = _compute_smile_confidence(blendshapes, lm)

                # ── 4. Stress Detection ──
                blink_detected = _detect_blink(blendshapes)
                result["blink_detected"] = blink_detected
                result["stress_indicator"] = _compute_stress(
                    blendshapes, blink_detected, result["smile_score"]
                )

                # ── 9. Nervous Behavior ──
                result["nervousness_indicator"] = _compute_nervousness(
                    blendshapes, lm, result["head_yaw"], result["stress_indicator"]
                )

                # ── 7. Head Movement Velocity (with engine history) ──
                engine.add_frame(result)
                head_mv = engine.compute_head_movement_velocity()
                result["head_movement_velocity"] = head_mv["overall"]
                result["head_movement_detail"] = head_mv

                # ── 8. Blink Rate from engine ──
                result["blink_rate"] = round(engine.compute_blink_rate(), 1)

        except Exception as e:
            logger.error("Face analysis error: %s", e)
            result["error"] = f"Face analysis error: {str(e)[:80]}"

    # ── POSTURE ANALYSIS ──
    pose_landmarker = _get_pose_landmarker()
    if pose_landmarker:
        try:
            pose_result = pose_landmarker.detect(mp_image)
            if pose_result.pose_landmarks:
                lm_pose = pose_result.pose_landmarks[0]
                # ── 3. Posture Score ──
                result["posture_score"] = _compute_posture(lm_pose)
            else:
                if result["face_detected"] and abs(result["head_yaw"]) < 15:
                    result["posture_score"] = 70
        except Exception:
            pass

    # ── 5. Engagement Score (composite) ──
    result["engagement_score"] = _compute_engagement(result)

    # ── 8. Attention Score ──
    result["attention_score"] = _compute_attention(result, engine)

    return result


# ──────────────────────────────────────────────
# COMPUTATION FUNCTIONS
# ──────────────────────────────────────────────

def _extract_blendshapes(face_result) -> dict:
    """Extract blendshape scores into a flat dict."""
    bs = {}
    if face_result.face_blendshapes and len(face_result.face_blendshapes) > 0:
        for b in face_result.face_blendshapes[0]:
            # Map category name -> score
            name = b.category_name
            # Convert camelCase to snake_case
            s = ""
            for c in name:
                if c.isupper() and s:
                    s += "_"
                s += c.lower()
            bs[s] = b.score
    return bs


def _extract_euler_angles(matrix) -> tuple:
    """Extract yaw, pitch, roll from 4x4 transformation matrix."""
    ry = -math.asin(matrix[2][0])
    rx = math.atan2(matrix[2][1] / math.cos(ry), matrix[2][2] / math.cos(ry))
    rz = math.atan2(matrix[1][0] / math.cos(ry), matrix[0][0] / math.cos(ry))
    # Clamp to avoid NaN
    ry = max(-math.pi / 2, min(math.pi / 2, ry))
    return ry, rx, rz


def _compute_eye_contact(yaw: float, pitch: float, roll: float, lm) -> int:
    """Score 0-100: how well candidate maintains eye contact with camera."""
    # Yaw penalty (looking left/right)
    yaw_deg = math.degrees(yaw)
    pitch_deg = math.degrees(pitch)
    roll_deg = math.degrees(roll)

    yaw_penalty = min(abs(yaw_deg) * 2.5, 50)
    pitch_penalty = min(abs(pitch_deg) * 2, 30)
    roll_penalty = min(abs(roll_deg) * 1.5, 20)

    # Nose offset from center (secondary measure)
    nose_tip = lm[1]
    nose_offset = abs(nose_tip.x - 0.5) * 100
    offset_penalty = min(nose_offset * 0.8, 20)

    score = 100 - yaw_penalty - pitch_penalty - roll_penalty - offset_penalty
    return max(0, min(100, int(score)))


def _classify_expression(bs: dict, lm) -> dict:
    """Classify expression using blendshapes and landmark geometry."""
    smile_l = bs.get("mouth_smile_left", 0)
    smile_r = bs.get("mouth_smile_right", 0)
    brow_down_l = bs.get("brow_down_left", 0)
    brow_down_r = bs.get("brow_down_right", 0)
    jaw_open = bs.get("jaw_open", 0)
    brow_inner_up = bs.get("brow_inner_up", 0)
    mouth_frown_l = bs.get("mouth_frown_left", 0)
    mouth_frown_r = bs.get("mouth_frown_right", 0)

    avg_smile = (smile_l + smile_r) / 2
    avg_frown = (mouth_frown_l + mouth_frown_r) / 2
    avg_brow_down = (brow_down_l + brow_down_r) / 2

    # Happy / positive
    if avg_smile > 0.15 and avg_smile > avg_frown:
        intensity = min(99, int(avg_smile * 120))
        return {"label": "positive", "confidence": max(50, intensity)}

    # Angry / stressed (brow down + lip press)
    if avg_brow_down > 0.3 and avg_frown > 0.1:
        intensity = min(99, int((avg_brow_down * 0.6 + avg_frown * 0.4) * 120))
        return {"label": "negative", "confidence": max(50, intensity)}

    # Surprised / engaged
    if brow_inner_up > 0.4 and jaw_open > 0.2:
        intensity = min(99, int((brow_inner_up * 0.5 + jaw_open * 0.5) * 100))
        return {"label": "positive", "confidence": max(50, intensity)}

    # Sad
    if avg_frown > 0.2 and brow_inner_up > 0.2:
        intensity = min(99, int((avg_frown * 0.5 + brow_inner_up * 0.5) * 100))
        return {"label": "negative", "confidence": max(50, intensity)}

    return {"label": "neutral", "confidence": 65}


def _compute_smile_confidence(bs: dict, lm) -> int:
    """Score 0-99 for smile genuineness using blendshapes + cheek raise."""
    smile_l = bs.get("mouth_smile_left", 0)
    smile_r = bs.get("mouth_smile_right", 0)
    cheek_squint_l = bs.get("cheek_squint_left", 0)
    cheek_squint_r = bs.get("cheek_squint_right", 0)
    mouth_stretch_l = bs.get("mouth_stretch_left", 0)
    mouth_stretch_r = bs.get("mouth_stretch_right", 0)

    avg_smile = (smile_l + smile_r) / 2
    avg_cheek = (cheek_squint_l + cheek_squint_r) / 2
    avg_stretch = (mouth_stretch_l + mouth_stretch_r) / 2

    # Duchenne smile: smile + cheek raise (eye crinkling)
    duchenne = avg_smile * 0.5 + avg_cheek * 0.3 + avg_stretch * 0.2
    score = min(99, int(duchenne * 150))
    return score


def _detect_blink(bs: dict) -> bool:
    """Detect a blink from blendshape values."""
    blink_l = bs.get("eye_blink_left", 0)
    blink_r = bs.get("eye_blink_right", 0)
    avg_blink = (blink_l + blink_r) / 2
    return avg_blink > 0.6


def _compute_stress(bs: dict, blink_detected: bool, smile_score: int) -> int:
    """Score 0-100: physiological stress indicators."""
    brow_down_l = bs.get("brow_down_left", 0)
    brow_down_r = bs.get("brow_down_right", 0)
    mouth_press_l = bs.get("mouth_press_left", 0)
    mouth_press_r = bs.get("mouth_press_right", 0)
    lip_tight = (mouth_press_l + mouth_press_r) / 2
    brow_furrow = (brow_down_l + brow_down_r) / 2

    # Low smile = tension
    smile_inverse = max(0, 1 - smile_score / 100) * 0.2

    stress = (brow_furrow * 0.35 + lip_tight * 0.25 + smile_inverse * 0.25 +
              (0.15 if blink_detected else 0))
    return max(0, min(100, int(stress * 100)))


def _compute_nervousness(
    bs: dict, lm, head_yaw_deg: float, stress: int
) -> int:
    """Score 0-100: nervous behavior indicators."""
    blink_l = bs.get("eye_blink_left", 0)
    blink_r = bs.get("eye_blink_right", 0)
    mouth_moved = bs.get("mouth_left", 0) + bs.get("mouth_right", 0) > 0.3
    jaw_side = bs.get("jaw_left", 0) + bs.get("jaw_right", 0)

    # Excessive head movement (looking around)
    head_sway = min(abs(head_yaw_deg) / 30, 1.0) * 0.2

    # Lip biting / pressing (oral self-soothing)
    lip_press = (bs.get("mouth_press_left", 0) + bs.get("mouth_press_right", 0)) / 2
    lip_bite = lip_press * 0.3

    # Rapid blinking (above normal 15-20 bpm)
    rapid_blink = ((blink_l + blink_r) / 2) * 0.15

    # Jaw tension / grinding
    jaw_tension = jaw_side * 0.15

    nervous = stress * 0.35 + head_sway * 100 + lip_bite * 100 + rapid_blink * 100 + jaw_tension * 100
    return max(0, min(100, int(nervous)))


def _compute_posture(lm) -> int:
    """Score 0-100: upright posture quality."""
    left_shoulder = lm[11]
    right_shoulder = lm[12]
    left_ear = lm[7]
    right_ear = lm[8]
    nose = lm[0]

    shoulder_slope = abs(left_shoulder.y - right_shoulder.y)
    ear_mid_x = (left_ear.x + right_ear.x) / 2
    shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2

    # Forward head protraction
    forward_head = max(0, ear_mid_x - shoulder_mid_x) * 5
    forward_head = min(forward_head, 30)

    # Shoulder asymmetry
    lateral_tilt = min(shoulder_slope * 5, 1.0) * 20

    # Nose-to-shoulder vertical alignment (slouching)
    shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
    nose_y = nose.y
    vertical_compression = max(0, nose_y - shoulder_mid_y + 0.15) * 100
    vertical_penalty = min(vertical_compression, 20)

    posture = 100 - lateral_tilt - forward_head - vertical_penalty
    return max(0, min(100, int(posture)))


def _compute_engagement(result: dict) -> int:
    """Composite engagement score from all dimensions. 0-99."""
    eye = result.get("eye_contact_score", 50)
    posture = result.get("posture_score", 50)
    expr_conf = result.get("expression_confidence", 50)
    is_positive = 100 if result.get("expression") == "positive" else 50 if result.get("expression") == "neutral" else 20
    attention = result.get("attention_score", 50)

    score = (
        eye * 0.30 +
        posture * 0.20 +
        is_positive * 0.15 +
        expr_conf * 0.10 +
        attention * 0.25
    )
    return max(0, min(99, int(score)))


def _compute_attention(result: dict, engine: VisualIntelligenceEngine) -> int:
    """Score 0-100: how attentive the candidate appears."""
    eye = result.get("eye_contact_score", 50)
    head_yaw = abs(result.get("head_yaw", 0))
    head_pitch = abs(result.get("head_pitch", 0))
    blink_rate = result.get("blink_rate", 0)

    # Looking away penalty
    gaze_penalty = min(head_yaw * 2, 30) + min(head_pitch * 1.5, 20)

    # Erratic head movement penalty
    head_mv = result.get("head_movement_velocity", 0)
    movement_penalty = min(head_mv * 3, 15)

    # Abnormal blink rate penalty (< 6 or > 40 bpm)
    if 0 < blink_rate < 6:
        blink_penalty = 10
    elif blink_rate > 40:
        blink_penalty = 10
    else:
        blink_penalty = 0

    score = eye - gaze_penalty * 0.3 - movement_penalty - blink_penalty
    return max(0, min(100, int(score)))


def _default_result() -> dict:
    return {
        "face_detected": False,
        "eye_contact_score": 0,
        "expression": "neutral",
        "expression_confidence": 0,
        "posture_score": 0,
        "stress_indicator": 0,
        "smile_score": 0,
        "head_yaw": 0.0,
        "head_pitch": 0.0,
        "head_roll": 0.0,
        "head_movement_velocity": 0.0,
        "head_movement_detail": {"yaw_velocity": 0, "pitch_velocity": 0, "roll_velocity": 0, "overall": 0},
        "engagement_score": 0,
        "attention_score": 0,
        "nervousness_indicator": 0,
        "blink_detected": False,
        "blink_rate": 0.0,
        "error": None,
    }


# ──────────────────────────────────────────────
# BATCH / VIDEO ANALYSIS
# ──────────────────────────────────────────────

def analyze_frames(frame_images: list[bytes]) -> dict:
    """
    Analyze a batch of video frames and return aggregated metrics.
    """
    if not frame_images:
        return _default_video_result(0)

    frame_results = [analyze_frame(f) for f in frame_images]
    n = len(frame_results)
    face_detected = sum(1 for r in frame_results if r["face_detected"])

    if face_detected == 0:
        return _default_video_result(n)

    detected = [r for r in frame_results if r["face_detected"]]
    d = len(detected)

    def avg(key):
        return int(np.mean([r.get(key, 0) for r in detected]))

    expr_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for r in detected:
        expr_counts[r["expression"]] += 1

    dom_expr = max(expr_counts, key=expr_counts.get)
    pos_pct = expr_counts["positive"] / d * 100
    neu_pct = expr_counts["neutral"] / d * 100
    neg_pct = expr_counts["negative"] / d * 100

    # Aggregate head movement
    avg_yaw_vel = np.mean([r.get("head_movement_detail", {}).get("yaw_velocity", 0) for r in detected])
    avg_pitch_vel = np.mean([r.get("head_movement_detail", {}).get("pitch_velocity", 0) for r in detected])
    avg_roll_vel = np.mean([r.get("head_movement_detail", {}).get("roll_velocity", 0) for r in detected])
    avg_blink_rate = np.mean([r.get("blink_rate", 0) for r in detected])

    return {
        "engagementScore": avg("engagement_score"),
        "stressLevel": avg("stress_indicator"),
        "nervousnessIndicator": avg("nervousness_indicator"),
        "eyeContactPct": avg("eye_contact_score"),
        "positiveExpressionPct": int(pos_pct),
        "neutralExpressionPct": int(neu_pct),
        "negativeExpressionPct": int(neg_pct),
        "uprightPosturePct": avg("posture_score"),
        "smileConfidence": avg("smile_score"),
        "attentionScore": avg("attention_score"),
        "avgBlinkRate": round(float(avg_blink_rate), 1),
        "avgHeadYawVelocity": round(float(avg_yaw_vel), 1),
        "avgHeadPitchVelocity": round(float(avg_pitch_vel), 1),
        "avgHeadRollVelocity": round(float(avg_roll_vel), 1),
        "framesAnalyzed": n,
        "faceDetectedFrames": face_detected,
        "dominantExpression": dom_expr,
    }


def _default_video_result(frame_count: int) -> dict:
    return {
        "engagementScore": 0, "stressLevel": 0, "nervousnessIndicator": 0,
        "eyeContactPct": 0, "positiveExpressionPct": 0, "neutralExpressionPct": 0,
        "negativeExpressionPct": 0, "uprightPosturePct": 0,
        "smileConfidence": 0, "attentionScore": 0,
        "avgBlinkRate": 0.0,
        "avgHeadYawVelocity": 0.0, "avgHeadPitchVelocity": 0.0, "avgHeadRollVelocity": 0.0,
        "framesAnalyzed": frame_count, "faceDetectedFrames": 0,
        "dominantExpression": "neutral",
    }


def analyze_video(video_duration_seconds: float = 60.0) -> dict:
    """Legacy fallback — returns neutral defaults."""
    return {
        "engagementScore": 50, "stressLevel": 25, "nervousnessIndicator": 20,
        "eyeContactPct": 70, "positiveExpressionPct": 40, "neutralExpressionPct": 40,
        "negativeExpressionPct": 10, "uprightPosturePct": 75,
        "smileConfidence": 50, "attentionScore": 70,
        "avgBlinkRate": 15.0,
        "avgHeadYawVelocity": 2.0, "avgHeadPitchVelocity": 1.5, "avgHeadRollVelocity": 0.5,
        "framesAnalyzed": 0, "faceDetectedFrames": 0,
        "dominantExpression": "neutral",
    }
