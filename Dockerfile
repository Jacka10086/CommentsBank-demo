FROM python:3.8

EXPOSE 5000

WORKDIR /app

# 复制当前目录下的所有文件到容器的/app目录
COPY . /app

# 安装requirements.txt文件中列出的所有依赖
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
