FROM ubuntu:22.04

RUN apt update \
    && apt install -y socat

WORKDIR /var/digger

COPY digger entrypoint.sh ./

RUN mkdir -p storage/passwords storage/secrets

RUN chmod +x digger entrypoint.sh \
    && chown -R nobody:nogroup storage

USER nobody

ENTRYPOINT [ "./entrypoint.sh" ]
