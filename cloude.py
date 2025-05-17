from google.cloud import vision
import io

# Path to your service account key JSON
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "my-service-account.json"

def detect_labels(path):
    """Detects labels in the image."""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.label_detection(image=image)
    labels = response.label_annotations

    print('Labels:')
    for label in labels:
        print(f"{label.description} (score: {label.score:.2f})")

    if response.error.message:
        raise Exception(f'{response.error.message}')

# Example usage
detect_labels('static/uploads/6b028c27-4dd2-44a0-bd5f-3d711de71623.jpeg')
