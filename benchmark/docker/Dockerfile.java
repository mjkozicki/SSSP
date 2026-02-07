# Benchmark image: compile and run Benchmark with /data/graph.txt
# Build from repo root: docker build -f benchmark/docker/Dockerfile.java .
# Uses Debian-based Temurin (non-alpine) for reliable pulls; use *-alpine if preferred.

FROM eclipse-temurin:21-jdk AS build
WORKDIR /src
COPY java/ java/
WORKDIR /src/java
RUN javac -d out *.java

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/java/out /app/out
ENV CLASSPATH=/app/out
ENV GRAPH_FILE=/data/graph.txt
ENTRYPOINT ["java", "sssp.Benchmark"]
