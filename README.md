*TODO*


# Build Docker image

```
docker build -t magnet-ai .
```


Note: If the application is hosted on a path other than the root of the domain, it is necessary to pass `WEB_BASE_PATH` argument in order for documentation page work correctly. It should start and end with "/".

docker build --build-arg WEB_BASE_PATH=/apps/magnet-ai/ -t magnet-ai .

# Run as a Docker image


```
docker run -d -p 8000:8000 --env-file=.env magnet-ai
```


