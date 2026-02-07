# Benchmark image: build benchmark binary
# Build from repo root: docker build -f benchmark/docker/Dockerfile.go .

FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go/ go/
WORKDIR /src/go
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /app/benchmark ./cmd/benchmark

FROM alpine:3.20
COPY --from=build /app/benchmark /app/benchmark
ENV GRAPH_FILE=/data/graph.txt
ENTRYPOINT ["/app/benchmark"]
