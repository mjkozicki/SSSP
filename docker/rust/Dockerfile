# Build and test SSSP Rust library
# Build context: repo root. Build: docker build -f docker/rust/Dockerfile .

FROM rust:1.83-alpine AS build
WORKDIR /src

# Install minimal deps for static linking (optional)
RUN apk add --no-cache musl-dev

# Copy manifest first for better cache (re-run only when deps change)
COPY rust/Cargo.toml rust/Cargo.lock* rust/
WORKDIR /src/rust
COPY rust/src/ ./src/
RUN cargo build --release && cargo test --release

# Minimal runtime: only if you add a binary; for lib, build stage is the artifact
FROM alpine:3.20 AS runtime
RUN apk add --no-cache libgcc
COPY --from=build /src/rust/target/release/*.so /app/ 2>/dev/null || true
WORKDIR /app
