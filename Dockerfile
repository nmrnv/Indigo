FROM mongo:4.4.11

ARG USER_ID
ARG GROUP_ID

RUN \
    userdel -f mongodb &&\
    if getent group mongodb ; then groupdel mongodb; fi &&\
    groupadd -g ${GROUP_ID} mongodb &&\
    useradd -l -u ${USER_ID} -g mongodb mongodb &&\
    install -d -m 0755 -o mongodb -g mongodb /home/mongodb &&\
    chmod -R 755 /data

USER mongodb