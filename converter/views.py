from django.shortcuts import render
from django.http import HttpResponse
from PIL import Image
import os, io

def index(request):
    error_msg = None

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

                if target_kb and target_kb.isdigit() and pil_fmt == 'JPEG':
                    target_bytes = int(target_kb) * 1024
                    low, high = 1, 95
                    best_quality = 85

                    for _ in range(10):
                        mid = (low + high) // 2
                        buf = io.BytesIO()
                        img.save(buf, format='JPEG', quality=mid, optimize=True)
                        if buf.tell() <= target_bytes:
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
                original_name = os.path.splitext(f.name)[0]
                download_name = original_name + '_converted.' + ext_out
                content_type = 'image/jpeg' if pil_fmt == 'JPEG' else 'image/png'

                response = HttpResponse(buffer, content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{download_name}"'
                return response

    return render(request, 'converter/index.html', {
        'error_msg': error_msg,
    })
