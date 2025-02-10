# Docker

Build in current dir
```bash
docker build -t raman-fitting-image .
```

Run the make example script as default in the docker image
```bash
docker run -it raman-fitting-image
```

Run other CLI commands through the docker image
```bash
docker run -it raman-fitting-image raman_fitting make index
```

For debugging or checking files in the docker image
```
docker run -it --entrypoint /bin/bash raman-fitting-image
```
