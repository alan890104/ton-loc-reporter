FROM python:3-slim

WORKDIR /
RUN pip3 install requests
COPY count_loc.py /count_loc.py

ENTRYPOINT ["python", "/count_loc.py"]
