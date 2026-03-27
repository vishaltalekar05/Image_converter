from django.shortcuts import render
from PIL import Image
import os, io
from django.conf import settings

def index(request):
    converted_url = None
    error_msg = None
    orig_size = None
    conv_size = None

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

                original_name = os.path.splitext(f.name)[0]
                name = original_name + '_converted.' + ext_out
                os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
                save_path = os.path.join(settings.MEDIA_ROOT, name)

                if target_kb and target_kb.isdigit() and pil_fmt == 'JPEG':
                    # Target size ke liye quality dhundho
                    target_bytes = int(target_kb) * 1024
                    low, high = 1, 95
                    best_quality = 85

                    for _ in range(10):
                        mid = (low + high) // 2
                        buffer = io.BytesIO()
                        img.save(buffer, format='JPEG', quality=mid, optimize=True)
                        size = buffer.tell()

                        if size <= target_bytes:
                            best_quality = mid
                            low = mid + 1
                        else:
                            high = mid - 1

                    img.save(save_path, format='JPEG', quality=best_quality, optimize=True)

                elif pil_fmt == 'JPEG':
                    img.save(save_path, format='JPEG', quality=85, optimize=True)

                else:
                    img.save(save_path, format='PNG', optimize=True)

                orig_size = round(f.size / 1024, 1)
                conv_size = round(os.path.getsize(save_path) / 1024, 1)
                converted_url = settings.MEDIA_URL + name

    return render(request, 'converter/index.html', {
        'converted_url': converted_url,
        'error_msg': error_msg,
        'orig_size': orig_size,
        'conv_size': conv_size,
    })