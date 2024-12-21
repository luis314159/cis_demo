import qrcode
import os

def generate_qr():
    # Define la URL del QR
    ip = "192.168.2.26"
    port = "8080"
    qr_url = f"http://{ip}:{port}/apk/current_apk.apk"  # Reemplaza con tu IP y puerto

    # Ruta donde se guardará la imagen generada
    output_dir = "./static/img"
    output_file = "generated_qr.png"

    # Crear el directorio si no existe
    os.makedirs(output_dir, exist_ok=True)

    # Generar el código QR
    qr_image = qrcode.make(qr_url)

    # Guardar el QR en el archivo
    qr_path = os.path.join(output_dir, output_file)
    qr_image.save(qr_path)

    print(f"QR generado y guardado en: {qr_path}")

if __name__ == "__main__":
    generate_qr()