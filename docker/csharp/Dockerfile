# Build and test SSSP C# library
# Build context: repo root. Build: docker build -f docker/csharp/Dockerfile .

FROM mcr.microsoft.com/dotnet/sdk:8.0-alpine AS build
WORKDIR /src

# Restore (cached unless csproj changes)
COPY csharp/SSSP.csproj csharp/
COPY csharp/SSSP.Tests/SSSP.Tests.csproj csharp/SSSP.Tests/
RUN dotnet restore csharp/SSSP.Tests/SSSP.Tests.csproj

# Build and test
COPY csharp/ csharp/
WORKDIR /src/csharp
RUN dotnet build SSSP.Tests/SSSP.Tests.csproj -c Release --no-restore && \
    dotnet test SSSP.Tests/SSSP.Tests.csproj -c Release --no-build -v minimal

# Optional: minimal runtime stage with published output (library only; no entrypoint)
FROM mcr.microsoft.com/dotnet/runtime:8.0-alpine AS runtime
WORKDIR /app
COPY --from=build /src/csharp/bin/Release/net8.0/ ./
# Library image: no CMD; use as base or copy DLLs
