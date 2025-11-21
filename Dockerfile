FROM debian:trixie-slim

# Update and install dependencies.
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y \
        make \
        git \
        build-essential \
        python3 \
        python3-dev \
        python3-venv \
        cython3

# Clone needed app files.
WORKDIR /app
COPY /submodules ./submodules
COPY /setup ./setup
COPY /utils ./utils
COPY /data ./data
COPY /scenes ./scenes
COPY requirements.txt main.py ./

# Created Python virtual environment. Update PATH and VIRTUAL_ENV environment variables to avoid needing to activate the virtual environment.
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install required Python packages.
RUN pip install -r requirements.txt

# Build and install rpi-rgb-led-matrix Python package.
WORKDIR /app/submodules/rpi-rgb-led-matrix
RUN make build-python PYTHON=$(which python) && make install-python PYTHON=$(which python)

# Clean up cache and temp files.
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Return to main app folder.
WORKDIR /app

# Start app.
ENTRYPOINT ["python", "main.py"]
