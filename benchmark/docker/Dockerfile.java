# Benchmark image: compile and run Benchmark with /data/graph.txt
# Build from repo root: docker build -f benchmark/docker/Dockerfile.java .

FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /src
COPY java/ java/
WORKDIR /src/java
RUN javac -d out *.java

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /src/java/out /app/out
ENV CLASSPATH=/app/out
ENV GRAPH_FILE=/data/graph.txt
ENTRYPOINT ["java", "sssp.Benchmark"]
