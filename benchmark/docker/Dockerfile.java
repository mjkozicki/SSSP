# Benchmark image: compile and run Benchmark with /data/graph.txt
# Build from repo root: docker build -f benchmark/docker/Dockerfile.java .
# Optional: set OTEL_EXPORTER_OTLP_ENDPOINT to send traces to SigNoz.

FROM maven:3.9-eclipse-temurin-21-alpine AS build
WORKDIR /src
COPY java/ java/
WORKDIR /src/java
RUN mvn -q -B package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/java/target/classes /app/classes
COPY --from=build /src/java/target/lib /app/lib
ENV CLASSPATH=/app/classes:/app/lib/*
ENV GRAPH_FILE=/data/graph.txt
ENTRYPOINT ["java", "sssp.Benchmark"]
