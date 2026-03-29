from django.shortcuts import render
from django.http import FileResponse
from PIL import Image
import os
import tempfile

def upload_and_convert(request):

    if request.method == 'POST' and request.FILES['image']:
        uploaded_file = request.FILES['image']
        target_format = request.POST['format']

        # Save temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_file.close()

        # Open image
        img = Image.open(temp_file.name)

        # Convert
        new_file = tempfile.NamedTemporaryFile(delete=False, suffix='.' + target_format.lower())
        
        if target_format == "JPEG":
            img = img.convert("RGB")

        img.save(new_file.name, target_format)

        # 🔥 DIRECT DOWNLOAD
        return FileResponse(open(new_file.name, 'rb'), as_attachment=True)

    return render(request, 'upload.html')