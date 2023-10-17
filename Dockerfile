FROM python:3.11-slim

COPY rainalarm.py /opt/rainalarm/
COPY requirements.txt /opt/rainalarm/
COPY .ssl/* /opt/rainalarm/.ssl/
RUN python -m pip install -r /opt/rainalarm/requirements.txt
WORKDIR /opt/rainalarm

ENTRYPOINT ["python", "/opt/rainalarm/rainalarm.py"]