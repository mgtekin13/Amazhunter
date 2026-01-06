# Python 3.11 slim kullanıyoruz
FROM python:3.11-slim

# Çalışma dizini
WORKDIR /app

# Gerekli dosyaları kopyala
COPY requirements.txt .
COPY Amazonbot.py .

# Gereksinimleri yükle
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "Amazonbot.py"]