FROM python:3.10-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


RUN python3 -m pip install git+https://github.com/HewlettPackard/cmf
ADD cmf_init.sh /app/cmf_init.sh
RUN chmod +x /app/cmf_init.sh
RUN /app/cmf_init.sh

CMD ["tail", "-f", "/dev/null"]


#ADD cmf_init.sh /app
#RUN bash cmf_init.sh 
#RUN cmf init show
#ENTRYPOINT ["python", "test.py"]
