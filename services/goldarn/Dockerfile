FROM ubuntu:22.04@sha256:b492494d8e0113c4ad3fe4528a4b5ff89faa5331f7d52c5c138196f69ce176a6 as setup

RUN apt -y update && apt -y install wget libseccomp-dev gcc

WORKDIR /
RUN wget https://github.com/yudai/gotty/releases/download/v1.0.1/gotty_linux_amd64.tar.gz
RUN tar xvf gotty_linux_amd64.tar.gz

ADD runner/main.c .
RUN gcc main.c -lseccomp -o runner

FROM rust:1.72@sha256:e18a590e3b63b971a1d5f9d91c89ac7d562a9c20279f8776dee8e2d34fc4ea52 as app

RUN apt -y update && apt -y install parallel

WORKDIR /app
ADD app/Cargo.toml app/Cargo.lock app/rust-toolchain .
RUN mkdir -p src && echo "//" > src/lib.rs
RUN cargo build  --release
RUN rm -rf src

ADD app/src ./src

COPY --from=setup /gotty /gotty
COPY --from=setup /runner /runner

RUN chmod u+s,g+s /runner

ADD gotty.crt /
ADD gotty.key /

RUN useradd -m -s /bin/false -u 1337 ctf

RUN mkdir -p /files && chown -R ctf:ctf /files && chmod 777 /files
RUN mkdir -p /cache && chown -R ctf:ctf /cache && chmod 777 /cache

ADD run.sh run_gotty.sh /
RUN chmod +x /run.sh /run_gotty.sh

USER ctf

CMD [ "/run.sh" ]
