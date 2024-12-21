import qrcode
import os
import socket
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def get_current_ip():
    """Obtiene la IP actual de la máquina."""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.error as e:
        print(f"Error obteniendo la IP: {e}")
        return "127.0.0.1"  # Default a localhost si falla

def generate_qr():
    # Obtiene la IP dinámica
    ip = get_current_ip()
    port = "8080"
    qr_url = f"http://{ip}:{port}/apk/current_app.apk"  # URL del QR dinámico

    # Ruta donde se guardará la imagen generada
    output_dir = "./static/qr"
    output_file = "generated_qr.png"

    # Crear el directorio si no existe
    os.makedirs(output_dir, exist_ok=True)

    # Generar el código QR
    qr_image = qrcode.make(qr_url)

    # Guardar el QR en el archivo
    qr_path = os.path.join(output_dir, output_file)
    qr_image.save(qr_path)

    print(f"QR generado y guardado en: {qr_path}")
    print(f"Contenido del QR: {qr_url}")

    return qr_path


def generate_pdf(qr_path):
    # Ruta donde se guardará el PDF generado
    pdf_output_dir = "./static/documents"
    pdf_output_file = "qr.pdf"

    # Crear el directorio si no existe
    os.makedirs(pdf_output_dir, exist_ok=True)

    # Ruta del logo
    logo_path = "./static/images/logo.jpg"

    # Tamaño de la página
    page_width, page_height = letter

    # Crear el PDF
    pdf_path = os.path.join(pdf_output_dir, pdf_output_file)
    c = canvas.Canvas(pdf_path, pagesize=letter)

    # Agregar el logo centrado
    if os.path.exists(logo_path):
        logo_width = 400
        logo_height = (191 / 1128) * logo_width  # Mantén la proporción
        logo_x = (page_width - logo_width) / 2  # Coordenada X centrada
        logo_y = page_height - logo_height - 50  # Un margen desde la parte superior
        c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height)
    else:
        print("Logo no encontrado. Asegúrate de que el archivo esté en la ruta especificada.")

    # Agregar el QR centrado
    if os.path.exists(qr_path):
        qr_size = 200  # Tamaño del QR cuadrado
        qr_x = (page_width - qr_size) / 2  # Coordenada X centrada
        qr_y = 300  # Posición Y del QR
        c.drawImage(qr_path, qr_x, qr_y, width=qr_size, height=qr_size)
    else:
        print("QR no encontrado. Asegúrate de que el QR se haya generado correctamente.")

    # Agregar texto descriptivo centrado
    c.setFont("Helvetica", 12)
    text = "Escanea el código QR para descargar la APK."
    text_width = c.stringWidth(text, "Helvetica", 12)
    text_x = (page_width - text_width) / 2  # Coordenada X centrada
    text_y = qr_y - 20  # Justo debajo del QR
    c.drawString(text_x, text_y, text)

    # Guardar el PDF
    c.save()

    print(f"PDF generado y guardado en: {pdf_path}")

if __name__ == "__main__":
    qr_path = generate_qr()
    generate_pdf(qr_path)