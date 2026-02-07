# Build and test SSSP Go module; produce minimal runtime image
# Build context: repo root. Build: docker build -f docker/go/Dockerfile .

FROM golang:1.22-alpine AS build
RUN apk add --no-cache git ca-certificates
WORKDIR /src

# Cache go mod (re-run only when go.mod changes)
COPY go/go.mod go/
WORKDIR /src/go
RUN go mod download 2>/dev/null || true

# Build and test
COPY go/ .
RUN go test -v -ldflags="-s -w" ./...

# Minimal runtime (no binary by default; use for go test or add a main)
FROM alpine:3.20 AS runtime
RUN apk add --no-cache ca-certificates
# Copy a binary here if you add cmd/ main:
# COPY --from=build /go/bin/sssp /app/sssp
WORKDIR /app
