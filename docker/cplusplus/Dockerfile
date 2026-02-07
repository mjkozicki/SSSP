# Build and test SSSP C++ library
# Build context: repo root. Build: docker build -f docker/cplusplus/Dockerfile .

FROM alpine:3.20 AS build
RUN apk add --no-cache build-base cmake

WORKDIR /src
COPY cplusplus/ cplusplus/
WORKDIR /src/cplusplus
RUN mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    cmake --build . && ctest --output-on-failure

# Minimal runtime (optional: run the test binary or ship headers/libs)
FROM alpine:3.20 AS runtime
RUN apk add --no-cache libstdc++
COPY --from=build /src/cplusplus/build/sssp_test /app/sssp_test 2>/dev/null || true
WORKDIR /app
