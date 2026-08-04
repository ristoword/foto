FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    fontconfig \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -f

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Pacchetti musica preinstallati stile iMovie / Canva / CapCut (royalty-free)
RUN python music_packs.py || true

CMD exec streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
