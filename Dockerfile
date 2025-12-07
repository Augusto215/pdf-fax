# Usa uma imagem Python leve como base
FROM python:3.11-slim

# Variáveis de ambiente para o WeasyPrint (garante que as bibliotecas sejam encontradas)
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

# Instala as dependências de sistema necessárias para o WeasyPrint
# Essas bibliotecas são essenciais para renderização de PDF/HTML
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libcairo2 \
        shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o código da aplicação e o logo
COPY main.py /app/
COPY angel_logo.png /app/

# Instala as dependências Python
# Instala WeasyPrint e FastAPI/Uvicorn
RUN pip install --no-cache-dir fastapi uvicorn[standard] weasyprint

# Comando para rodar a aplicação com Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]