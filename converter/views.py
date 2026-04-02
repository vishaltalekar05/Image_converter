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
                img = Image.open(f)
                pil_fmt = 'JPEG' if fmt == 'jpg' else 'PNG'
                ext_out = 'jpg' if fmt == 'jpg' else 'png'

                # ✅ RGBA fix for JPEG
                if pil_fmt == 'JPEG' and img.mode in ('RGBA', 'P', 'LA'):
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = bg

                buffer = io.BytesIO()

                # =========================
                # 🔥 JPEG COMPRESSION
                # =========================
                if target_kb and target_kb.isdigit() and pil_fmt == 'JPEG':
                    target_bytes = int(target_kb) * 1024
                    original_bytes = f.size

                    if original_bytes <= target_bytes:
                        # already small → don't increase
                        img.save(buffer, format='JPEG', quality=75, optimize=True)
                    else:
                        low, high = 5, 95
                        best_data = None

                        while low <= high:
                            mid = (low + high) // 2
                            temp_buf = io.BytesIO()
                            img.save(temp_buf, format='JPEG', quality=mid, optimize=True)
                            size = temp_buf.tell()

                            if size <= target_bytes:
                                best_data = temp_buf.getvalue()
                                low = mid + 1
                            else:
                                high = mid - 1

                        if best_data:
                            buffer.write(best_data)
                        else:
                            img.save(buffer, format='JPEG', quality=5, optimize=True)

                elif pil_fmt == 'JPEG':
                    img.save(buffer, format='JPEG', quality=85, optimize=True)

                # =========================
                # 🔥 PNG COMPRESSION (FIXED)
                # =========================
                elif pil_fmt == 'PNG':
                    target_bytes = int(target_kb) * 1024 if target_kb.isdigit() else None

                    if target_bytes:
                        width, height = img.size

                        while True:
                            temp_buf = io.BytesIO()
                            img.save(temp_buf, format='PNG', optimize=True, compress_level=9)
                            size = temp_buf.tell()

                            if size <= target_bytes or width < 100:
                                buffer.write(temp_buf.getvalue())
                                break

                            # 🔥 resize reduce
                            width = int(width * 0.9)
                            height = int(height * 0.9)
                            img = img.resize((width, height))

                    else:
                        img.save(buffer, format='PNG', optimize=True, compress_level=9)

                buffer.seek(0)

                # =========================
                # Preview + Download
                # =========================
                original_name = os.path.splitext(f.name)[0]
                download_name = original_name + '_converted.' + ext_out
                ext_out_mime = 'jpeg' if pil_fmt == 'JPEG' else 'png'

                conv_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                converted_url = f'data:image/{ext_out_mime};base64,{conv_b64}'

                f.seek(0)
                orig_b64 = base64.b64encode(f.read()).decode('utf-8')
                orig_mime = 'jpeg' if ext in ['jpg', 'jpeg'] else 'png'
                original_preview = f'data:image/{orig_mime};base64,{orig_b64}'

                return render(request, 'converter/index.html', {
                    'error_msg': None,
                    'converted_url': converted_url,
                    'original_preview': original_preview,
                    'download_url': converted_url,
                    'download_name': download_name,
                    'orig_size': round(f.size / 1024, 1),
                    'conv_size': round(len(buffer.getvalue()) / 1024, 1),
                })

    return render(request, 'converter/index.html', {
        'error_msg': error_msg,
    })