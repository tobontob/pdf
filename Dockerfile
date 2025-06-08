FROM ubuntu:20.04

# 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    xvfb \
    x11vnc \
    novnc \
    wget \
    unzip \
    fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt .
COPY converters ./converters
COPY app.py .

# Python 패키지 설치
RUN pip3 install --no-cache-dir -r requirements.txt

# Xvfb 및 VNC 설정
ENV DISPLAY=:99
ENV RESOLUTION=1920x1080x24

# 스크립트 생성
RUN echo '#!/bin/bash\n\
Xvfb $DISPLAY -screen 0 $RESOLUTION &\n\
x11vnc -display $DISPLAY -forever -shared &\n\
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 &\n\
python3 app.py\n\
' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 5900 6080 5000

CMD ["/app/start.sh"] 