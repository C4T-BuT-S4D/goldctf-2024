FROM ubuntu:22.04@sha256:b492494d8e0113c4ad3fe4528a4b5ff89faa5331f7d52c5c138196f69ce176a6 as gotty

RUN apt -y update && apt -y install wget

WORKDIR /
RUN wget https://github.com/yudai/gotty/releases/download/v2.0.0-alpha.3/gotty_2.0.0-alpha.3_linux_amd64.tar.gz
RUN tar xvf gotty_2.0.0-alpha.3_linux_amd64.tar.gz

FROM rust:1.72@sha256:e18a590e3b63b971a1d5f9d91c89ac7d562a9c20279f8776dee8e2d34fc4ea52 as app

WORKDIR /app
ADD app/Cargo.toml app/Cargo.lock app/rust-toolchain .
RUN mkdir src && echo "//" > src/lib.rs
RUN cargo build

ADD app/src ./src
RUN cargo build --release

FROM ubuntu:22.04@sha256:b492494d8e0113c4ad3fe4528a4b5ff89faa5331f7d52c5c138196f69ce176a6

COPY --from=gotty /gotty /gotty
COPY --from=app /app/target/release/abilene /abilene

RUN echo "nobody:x:1337:1337:::" > /etc/passwd
RUN echo "nobody::1337:nobody" > /etc/group

RUN mkdir -p /files && chown -R nobody:nobody /files

WORKDIR /app
USER nobody

ADD --chown=nobody gotty.crt /
ADD --chown=nobody gotty.key /

CMD [ \
    "/gotty", \
    "--port", "1337", \
    "--permit-write", \
    "--close-timeout", "5", \
    "--tls", \
    "--tls-crt", "/gotty.crt", \
    "--tls-key", "/gotty.key", \
    "/abilene" \
]
