# Stage 1: build liboqs with only the algorithms we need (much faster than full build)
FROM python:3.11-slim-bookworm AS liboqs-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git cmake build-essential libssl-dev ninja-build \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs /tmp/liboqs \
    && cmake -S /tmp/liboqs -B /tmp/liboqs/build \
        -GNinja \
        -DBUILD_SHARED_LIBS=ON \
        -DOQS_DIST_BUILD=ON \
        -DOQS_ALGS_ENABLED=STD \
    && cmake --build /tmp/liboqs/build -j "$(nproc)" \
    && cmake --install /tmp/liboqs/build \
    && rm -rf /tmp/liboqs

# Stage 2: application image
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=liboqs-builder /usr/local/lib/ /usr/local/lib/
COPY --from=liboqs-builder /usr/local/include/ /usr/local/include/

ENV LD_LIBRARY_PATH=/usr/local/lib
ENV OQS_INSTALL_PATH=/usr/local

WORKDIR /app

COPY requirements.txt .
# liboqs-python should detect pre-installed liboqs via OQS_INSTALL_PATH
RUN pip install --no-cache-dir -r requirements.txt

COPY pq_voting ./pq_voting
COPY static ./static
# liboqs-js WASM must be present under static/vendor/liboqs-js (see static/vendor/README.md)
COPY tests ./tests

ENV PQ_VOTING_DATA_DIR=/app/data
RUN mkdir -p /app/data/keys

EXPOSE 8000

CMD ["uvicorn", "pq_voting.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
