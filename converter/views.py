from django.shortcuts import render
from PIL import Image
import os, io
from django.conf import settings
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key    = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
)

def index(request):
    error_msg = None
    orig_size = None
    conv_size = None
    converted_url = None
    download_url = None
    converted_name = None

    if request.method == 'POST':
        f = request.FILES.get('image')
        fmt = request.POST.get('format', 'jpg').lower()
        target_kb = request.POST.get('target_kb', '').strip()

        if f:
            ext = os.path.splitext(f.name)[1].lower().replace('.', '')

            if (ext in ['jpg', 'jpeg'] and fmt == 'jpg') or (ext == 'png' and fmt == 'png'):
                error_msg = 'Image is already ' + ext.upper() + '! Please select a different format.'
            else:
                img = Image.open(f)
                pil_fmt = 'JPEG' if fmt == 'jpg' else 'PNG'
                ext_out = 'jpg' if fmt == 'jpg' else 'png'

                if pil_fmt == 'JPEG' and img.mode in ('RGBA', 'P', 'LA'):
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = bg

                buffer = io.BytesIO()
                orig_size = round(f.size / 1024, 1)

                if target_kb and target_kb.isdigit() and pil_fmt == 'JPEG':
                    target_bytes = int(target_kb) * 1024
                    low, high = 1, 95
                    best_quality = 85

                    for _ in range(10):
                        mid = (low + high) // 2
                        buf = io.BytesIO()
                        img.save(buf, format='JPEG', quality=mid, optimize=True)
                        size = buf.tell()
                        if size <= target_bytes:
                            best_quality = mid
                            low = mid + 1
                        else:
                            high = mid - 1

                    img.save(buffer, format='JPEG', quality=best_quality, optimize=True)
                elif pil_fmt == 'JPEG':
                    img.save(buffer, format='JPEG', quality=85, optimize=True)
                else:
                    img.save(buffer, format='PNG', optimize=True)

                buffer.seek(0)
                conv_size = round(len(buffer.getvalue()) / 1024, 1)

                # Cloudinary pe upload karo
                original_name = os.path.splitext(f.name)[0]
                upload_result = cloudinary.uploader.upload(
                    buffer,
                    public_id=original_name + '_converted',
                    format=ext_out,
                    overwrite=True,
                )

                converted_url = upload_result['secure_url']
                download_url = upload_result['secure_url']
                converted_name = original_name + '_converted.' + ext_out

    return render(request, 'converter/index.html', {
        'error_msg': error_msg,
        'orig_size': orig_size,
        'conv_size': conv_size,
        'converted_url': converted_url,
        'download_url': download_url,
        'converted_name': converted_name,
    })