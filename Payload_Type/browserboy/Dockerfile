FROM itsafeaturemythic/mythic_python_base:latest

WORKDIR /Mythic/

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt

CMD ["python3", "main.py"]
