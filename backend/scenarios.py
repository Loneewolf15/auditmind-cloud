from datetime import datetime, timedelta

def generate_timestamp(minutes_ago: int) -> str:
    return (datetime.utcnow() - timedelta(minutes=minutes_ago)).isoformat() + "Z"

def get_scenarios() -> dict:
    """
    Returns demo scenarios with timestamps generated fresh at call time.
    Must be a function (not a module-level constant) so timestamps stay
    accurate in long-running processes instead of freezing at container start.
    """
    return {
    "clean_session": [
        {
            "event_id": "evt_cln_1",
            "user_id": "student_001",
            "institution": "Lagos CBT Centre",
            "session_id": "jamb_2026_clean_001",
            "session_type": "exam",
            "event_type": "verification_pass",
            "confidence": 0.97,
            "timestamp": generate_timestamp(40),
            "location": "Lagos, NG",
            "device": "webcam",
            "flag": "none"
        },
        {
            "event_id": "evt_cln_2",
            "user_id": "student_001",
            "institution": "Lagos CBT Centre",
            "session_id": "jamb_2026_clean_001",
            "session_type": "exam",
            "event_type": "verification_pass",
            "confidence": 0.95,
            "timestamp": generate_timestamp(30),
            "location": "Lagos, NG",
            "device": "webcam",
            "flag": "none"
        },
        {
            "event_id": "evt_cln_3",
            "user_id": "student_001",
            "institution": "Lagos CBT Centre",
            "session_id": "jamb_2026_clean_001",
            "session_type": "exam",
            "event_type": "verification_pass",
            "confidence": 0.94,
            "timestamp": generate_timestamp(20),
            "location": "Lagos, NG",
            "device": "webcam",
            "flag": "none"
        },
        {
            "event_id": "evt_cln_4",
            "user_id": "student_001",
            "institution": "Lagos CBT Centre",
            "session_id": "jamb_2026_clean_001",
            "session_type": "exam",
            "event_type": "verification_pass",
            "confidence": 0.91,
            "timestamp": generate_timestamp(10),
            "location": "Lagos, NG",
            "device": "webcam",
            "flag": "none"
        }
    ],
    "fraud_attempt": [
        {
            "event_id": "evt_frd_1",
            "user_id": "student_002",
            "institution": "Abuja Testing Center",
            "session_id": "jamb_2026_fraud_002",
            "session_type": "exam",
            "event_type": "verification_pass",
            "confidence": 0.92,
            "timestamp": generate_timestamp(45),
            "location": "Abuja, NG",
            "device": "webcam",
            "flag": "none"
        },
        {
            "event_id": "evt_frd_2",
            "user_id": "student_002",
            "institution": "Abuja Testing Center",
            "session_id": "jamb_2026_fraud_002",
            "session_type": "exam",
            "event_type": "verification_pass",
            "confidence": 0.89,
            "timestamp": generate_timestamp(35),
            "location": "Abuja, NG",
            "device": "webcam",
            "flag": "none"
        },
        {
            "event_id": "evt_frd_3",
            "user_id": "student_002",
            "institution": "Abuja Testing Center",
            "session_id": "jamb_2026_fraud_002",
            "session_type": "exam",
            "event_type": "anomaly_detected",
            "confidence": 0.41,
            "timestamp": generate_timestamp(25),
            "location": "Abuja, NG",
            "device": "webcam",
            "flag": "face_mismatch"
        },
        {
            "event_id": "evt_frd_4",
            "user_id": "student_002",
            "institution": "Abuja Testing Center",
            "session_id": "jamb_2026_fraud_002",
            "session_type": "exam",
            "event_type": "verification_fail",
            "confidence": 0.23,
            "timestamp": generate_timestamp(15),
            "location": "Abuja, NG",
            "device": "webcam",
            "flag": "proxy_candidate_suspected"
        }
    ],
    "traffic_audit": [
        {
            "event_id": "evt_trf_1",
            "user_id": "driver_A001",
            "institution": "Lagos-Ibadan Expressway",
            "session_id": "traffic_audit_004",
            "session_type": "traffic",
            "event_type": "verification_pass",
            "confidence": 0.96,
            "timestamp": generate_timestamp(55),
            "location": "Lagos Toll Gate 1, NG",
            "device": "plate_reader",
            "flag": "none"
        },
        {
            "event_id": "evt_trf_2",
            "user_id": "driver_A001",
            "institution": "Lagos-Ibadan Expressway",
            "session_id": "traffic_audit_004",
            "session_type": "traffic",
            "event_type": "verification_pass",
            "confidence": 0.91,
            "timestamp": generate_timestamp(40),
            "location": "Lagos Toll Gate 2, NG",
            "device": "plate_reader",
            "flag": "none"
        },
        {
            "event_id": "evt_trf_3",
            "user_id": "driver_A001",
            "institution": "Lagos-Ibadan Expressway",
            "session_id": "traffic_audit_004",
            "session_type": "traffic",
            "event_type": "anomaly_detected",
            "confidence": 0.52,
            "timestamp": generate_timestamp(22),
            "location": "Sagamu Interchange, NG",
            "device": "speed_camera",
            "flag": "impossible_travel_speed"
        },
        {
            "event_id": "evt_trf_4",
            "user_id": "driver_A001",
            "institution": "Lagos-Ibadan Expressway",
            "session_id": "traffic_audit_004",
            "session_type": "traffic",
            "event_type": "verification_fail",
            "confidence": 0.28,
            "timestamp": generate_timestamp(10),
            "location": "Ibadan North Checkpoint, NG",
            "device": "plate_reader",
            "flag": "plate_mismatch_suspected"
        }
    ],
    "ndpr_purge": [
        {
            "event_id": "evt_ndpr_1",
            "user_id": "user_pending_deletion",
            "institution": "Bank of Nigeria",
            "session_id": "jamb_2026_ndpr_003",
            "session_type": "kyc",
            "event_type": "verification_pass",
            "confidence": 0.98,
            "timestamp": generate_timestamp(120),
            "location": "Kano, NG",
            "device": "mobile",
            "flag": "none"
        },
        {
            "event_id": "evt_ndpr_2",
            "user_id": "user_pending_deletion",
            "institution": "Bank of Nigeria",
            "session_id": "jamb_2026_ndpr_003",
            "session_type": "kyc",
            "event_type": "verification_pass",
            "confidence": 0.97,
            "timestamp": generate_timestamp(110),
            "location": "Kano, NG",
            "device": "mobile",
            "flag": "none"
        }
    ]
}
