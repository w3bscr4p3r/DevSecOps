import os
import sys
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from cryptography.fernet import Fernet

# Configuração de Log
logging.basicConfig(
    filename='/app/logs/backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_alert(subject, message):
    msg = MIMEText(message)
    msg['Subject'] = f"[Backup System] {subject}"
    msg['From'] = "backup-system@empresa.com"
    msg['To'] = os.getenv('ALERT_EMAILS')
    
    try:
        with smtplib.SMTP(os.getenv('SMTP_SERVER'), os.getenv('SMTP_PORT')) as server:
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Falha no envio de email: {str(e)}")

def encrypt_file(file_path):
    cipher = Fernet(os.getenv('BACKUP_ENCRYPTION_KEY'))
    with open(file_path, 'rb') as f:
        encrypted_data = cipher.encrypt(f.read())
    with open(f"{file_path}.enc", 'wb') as f:
        f.write(encrypted_data)
    os.remove(file_path)

def check_disk_space():
    total, used, free = shutil.disk_usage("/backups")
    if (free // (2**30)) < int(os.getenv('MAX_BACKUP_SIZE_GB')):
        send_alert("Espaço em disco insuficiente", 
                  f"Espaço livre: {free // (2**30)}GB")
        return False
    return True

def main():
    try:
        if not check_disk_space():
            return
        
        # Lógica de backup existente + compressão
        backup_file = create_compressed_backup()
        
        # Criptografar backup
        encrypt_file(backup_file)
        
        # Aplicar política de retenção
        apply_retention_policy()
        
        logging.info("Backup concluído com sucesso")
        
    except Exception as e:
        logging.error(f"Erro crítico: {str(e)}")
        send_alert("Falha no Backup", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
