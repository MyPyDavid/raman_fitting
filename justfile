# Default recipe to display help information
default:
  @just --list

[group('docker')]
docker-build:
  docker build -t raman-fitting-image .

[group('docker')]
docker-run:
  docker run -it raman-fitting-image

[group('docker')]
docker-run-cli +args:
  docker run -it raman-fitting-image {{args}}

[group('docker')]
docker-debug:
  docker run -it --entrypoint /bin/bash raman-fitting-image
