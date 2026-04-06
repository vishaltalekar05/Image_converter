from django.shortcuts import render
from PIL import Image
import os, io, base64

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
                f.seek(0)
                orig_bytes = f.read()

                # File size check
                if len(orig_bytes) > 5 * 1024 * 1024:
                    return render(request, 'converter/index.html', {
                        'error_msg': 'File too large! Please upload image smaller than 5MB.',
                    })

                orig_mime = 'jpeg' if ext in ['jpg', 'jpeg'] else 'png'
                original_preview = 'data:image/' + orig_mime + ';base64,' + base64.b64encode(orig_bytes).decode('utf-8')

                f.seek(0)
                img = Image.open(f)
                img.load()

                # Large image resize
                if img.width > 1200 or img.height > 1200:
                    img.thumbnail((1200, 1200), Image.LANCZOS)

                pil_fmt = 'JPEG' if fmt == 'jpg' else 'PNG'
                ext_out = 'jpg' if fmt == 'jpg' else 'png'

                if pil_fmt == 'JPEG' and img.mode != 'RGB':
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        bg.paste(img, mask=img.split()[-1])
                    else:
                        bg.paste(img)
                    img = bg

                out = io.BytesIO()

                if target_kb and target_kb.isdigit() and pil_fmt == 'JPEG':
                    target_bytes = int(target_kb) * 1024
                    chosen = None

                    for q in range(95, 0, -1):
                        tmp = io.BytesIO()
                        img.save(tmp, format='JPEG', quality=q, optimize=True)
                        if tmp.tell() <= target_bytes:
                            chosen = tmp.getvalue()
                            break

                    if chosen:
                        out.write(chosen)
                    else:
                        img.save(out, format='JPEG', quality=1, optimize=True)

                elif pil_fmt == 'JPEG':
                    orig_buf = io.BytesIO()
                    img.save(orig_buf, format='JPEG', quality=85, optimize=True)
                    if orig_buf.tell() > len(orig_bytes):
                        for q in range(85, 0, -1):
                            tmp = io.BytesIO()
                            img.save(tmp, format='JPEG', quality=q, optimize=True)
                            if tmp.tell() <= len(orig_bytes):
                                out.write(tmp.getvalue())
                                break
                        else:
                            img.save(out, format='JPEG', quality=85, optimize=True)
                    else:
                        out.write(orig_buf.getvalue())

                else:
                    if target_kb and target_kb.isdigit():
                        target_bytes = int(target_kb) * 1024
                        scale = 1.0
                        while scale > 0.1:
                            tmp = io.BytesIO()
                            new_w = int(img.width * scale)
                            new_h = int(img.height * scale)
                            resized = img.resize((new_w, new_h), Image.LANCZOS)
                            resized.save(tmp, format='PNG', optimize=True)
                            if tmp.tell() <= target_bytes:
                                out.write(tmp.getvalue())
                                break
                            scale -= 0.05
                        else:
                            img.save(out, format='PNG', optimize=True)
                    else:
                        img.save(out, format='PNG', optimize=True)

                out.seek(0)
                data = out.getvalue()

                original_name = os.path.splitext(f.name)[0]
                download_name = original_name + '_converted.' + ext_out
                ext_mime = 'jpeg' if pil_fmt == 'JPEG' else 'png'
                converted_url = 'data:image/' + ext_mime + ';base64,' + base64.b64encode(data).decode('utf-8')

                return render(request, 'converter/index.html', {
                    'error_msg': None,
                    'converted_url': converted_url,
                    'original_preview': original_preview,
                    'download_url': converted_url,
                    'download_name': download_name,
                    'orig_size': round(len(orig_bytes) / 1024, 1),
                    'conv_size': round(len(data) / 1024, 1),
                })

    return render(request, 'converter/index.html', {
        'error_msg': error_msg,
    })