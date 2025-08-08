import os
from googleapiclient import discovery

API_KEY = os.getenv("GOOGLE_PERSPECTIVE_API_KEY", None)

client = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=API_KEY,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
)

def check_toxicity(text: str, threshold: float = 0.7) -> dict:
    if not text.strip():
        return {"allowed": True, "score": 0.0}

    analyze_request = {
        'comment': {'text': text},
        'requestedAttributes': {'TOXICITY': {}}
    }
    response = client.comments().analyze(body=analyze_request).execute()
    score = response['attributeScores']['TOXICITY']['summaryScore']['value']
    
    return {
        "allowed": score < threshold,
        "score": score,
        "content":  text
    }
