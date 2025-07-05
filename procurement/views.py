# procurement/views.py
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.lib.pagesizes import A4
from .models import PurchaseOrder


def download_po_barcode(request, po_id):
    po = PurchaseOrder.objects.get(id=po_id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    barcode = code128.Code128(po.po_number, barHeight=40)
    barcode.drawOn(p, 100, 700)
    p.setFont("Helvetica", 14)
    p.drawString(100, 750, f"PO Number: {po.po_number}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'PO-{po.po_number}-barcode.pdf')



