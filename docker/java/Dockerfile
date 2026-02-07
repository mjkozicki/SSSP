# Build and test SSSP Java (no Maven/Gradle)
# Build context: repo root. Build: docker build -f docker/java/Dockerfile .

FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /src

COPY java/ java/
WORKDIR /src/java
RUN javac -d out *.java && java -cp out sssp.Main

# Slim runtime with JRE (run Main or tests)
FROM eclipse-temurin:21-jre-alpine AS runtime
WORKDIR /app
COPY --from=build /src/java/out /app/out
ENV CLASSPATH=/app/out
# CMD ["java", "sssp.Main"]
