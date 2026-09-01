# Notes on Setup PeerMoA

List of deploy configs of the tool on various architectures.

### 01 - Setup Through Ollama bin

List of commands used to setup peerMoA on an ARM VM, no sudo permission.
- Using the `ollama bin` **not** the `systemcls service`.

```sh
# Downloading ollama binaries
curl -L https://github.com/ollama/ollama/releases/download/v0.21.0/ollama-linux-arm64.tar.zst -o ollama.tar.zst
# Extracting ollama
tar -xf ollama.tar.zst
# Launching it in background
nohup ./bin/ollama serve > ollama.log 2>&1 &

# --- The VM had python3.10 but ECLYPSE needed python3.11 so we are
# using uv to use python3.11

# Installing uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Using uv to install python3.11
uv venv --python 3.11 .venv

# Installing dependencies through uv
source .venv/bin/activate
uv pip install -r requirements.txt

# To run it without GPU specs
CUDA_VISIBLE_DEVICES="" python3 -u main.py
```

### 02 - Setup Ollama on GPU AMD Through Ollama Service

Open the configuration of ollama service:

```sh
# Opening config of the ollama service
sudo systemctl edit ollama.service
```

Into the file define the variable:

```sh
[Service]
Environment="HSA_OVERRIDE_GFX_VERSION=10.3.0"
```

After that we can restart the service.

```sh
sudo systemctl daemon-reload
sudo systemctl restart ollama
```
