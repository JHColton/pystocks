# Python base image
FROM python:3.12-bullseye

# Working directory
WORKDIR /termstocks

# Copy the project files into the container
COPY . .

# Pip install uv, since Rust isn't installed
RUN pip install uv

# Install Python dependencies managed by `uv`
RUN uv sync

# Specify the default command to run your Python script
CMD ["uv", "run", "termstocks.py"]
