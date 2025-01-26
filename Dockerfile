# set base image (host OS)
FROM python:3.12

RUN addgroup -S nonroot \
    && adduser -S nonroot -G nonroot

USER nonroot

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY ./raman-fitting ./raman-fitting

# copy setup.cfg to work dir
# COPY setup.cfg .
# COPY setup.py .
# install package test, maybe not possible because only src
# RUN pip install -e ./


# install dependencies
RUN pip install -r requirements.txt

RUN pip install --upgrade build
RUN build ./
RUN pip install -e  ./

# copy the content of the local src directory to the working directory
#COPY src/ .

# command to run on container start
CMD [ "raman_fitting run examples" ]
