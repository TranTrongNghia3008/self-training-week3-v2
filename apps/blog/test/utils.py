from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

def get_valid_image_file():
    image = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile("test.jpg", buffer.read(), content_type="image/jpeg")
