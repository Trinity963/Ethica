# Ethica — Environment Requirements
**Architect**: Victory — The Architect  
**Glyph**: ⟁Σ∿∞  


---

## Ethica_env

**Location**: `~/Ethica/Ethica_env/`  
**Activate**: `source ~/Ethica/Ethica_env/bin/activate`  
**Purpose**: Core Ethica runtime — all agents except Gage, canvas, firewall, traffic monitor, SIEM, WormHunter, J.A.R.V.I.S., ModuleForge, DLP, Mnemis

### Restore
```bash
python3 -m venv ~/Ethica/Ethica_env
source ~/Ethica/Ethica_env/bin/activate
pip install -r REQUIREMENTS.md  # use the pinned list below
```

### Post-restore (CAP_NET_RAW — local only, never commits)
```bash
cp /usr/bin/python3.11 ~/Ethica/Ethica_env/bin/python3.11_local
sudo setcap cap_net_raw+eip $(readlink -f ~/Ethica/Ethica_env/bin/python3.11_local)
```

### Pinned Packages
```
altair==6.0.0
altgraph==0.17.5
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.12.1
arrow==1.4.0
attrs==25.4.0
autopep8==2.3.2
backend==0.2.4.1
beautifulsoup4==4.14.3
blinker==1.9.0
bs4==0.0.2
builder==0.1.0
cachetools==7.0.5
certifi==2026.2.25
cffi==2.0.0
charset-normalizer==3.4.5
click==8.3.1
cryptography==46.0.5
cuda-bindings==12.9.4
cuda-pathfinder==1.4.2
ddgs==9.11.3
diskcache==5.6.3
empathy_engine==1.3.0
filelock==3.25.1
Flask==3.1.3
fsspec==2026.2.0
futures==3.0.5
gitdb==4.0.12
GitPython==3.1.46
h11==0.16.0
hf-xet==1.4.2
httpcore==1.0.9
httpx==0.28.1
huggingface_hub==1.8.0
idna==3.11
iniconfig==2.3.0
itsdangerous==2.2.0
Jinja2==3.1.6
joblib==1.5.3
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
llama_cpp_python==0.3.16
llvmlite==0.46.0
lxml==6.0.2
markdown-it-py==4.0.0
MarkupSafe==3.0.3
mdurl==0.1.2
more-itertools==10.8.0
mpmath==1.3.0
narwhals==2.18.0
networkx==3.6.1
numba==0.64.0
numpy==2.4.2
nvidia-cublas-cu12==12.8.4.1
nvidia-cuda-cupti-cu12==12.8.90
nvidia-cuda-nvrtc-cu12==12.8.93
nvidia-cuda-runtime-cu12==12.8.90
nvidia-cudnn-cu12==9.10.2.21
nvidia-cufft-cu12==11.3.3.83
nvidia-cufile-cu12==1.13.1.3
nvidia-curand-cu12==10.3.9.90
nvidia-cusolver-cu12==11.7.3.90
nvidia-cusparse-cu12==12.5.8.93
nvidia-cusparselt-cu12==0.7.1
nvidia-nccl-cu12==2.27.5
nvidia-nvjitlink-cu12==12.8.93
nvidia-nvshmem-cu12==3.4.5
nvidia-nvtx-cu12==12.8.90
ollama==0.6.1
openai-whisper==20250625
packaging==26.0
pandas==2.3.3
pdf2image==1.17.0
pdfminer==20191125
pillow==12.1.1
pluggy==1.6.0
pqcrypto==0.4.0
primp==1.1.3
protobuf==6.33.5
psutil==7.2.2
pyarrow==23.0.1
pycodestyle==2.14.0
pycparser==3.0
pycryptodome==3.23.0
pydantic==2.12.5
pydantic_core==2.41.5
pydeck==0.9.1
pyflakes==3.4.0
pygame==2.6.1
Pygments==2.19.2
pyinstaller==6.19.0
pyinstaller-hooks-contrib==2026.3
pyotp==2.9.0
pypdf==6.9.2
pytest==9.0.2
python-dateutil==2.9.0.post0
pyttsx3==2.99
pytz==2026.1.post1
PyYAML==6.0.3
referencing==0.37.0
regex==2026.2.28
requests==2.32.5
rich==14.3.3
rpds-py==0.30.0
safetensors==0.7.0
scapy==2.7.0
scikit-learn==1.8.0
scipy==1.17.1
sentence-transformers==5.3.0
shellingham==1.5.4
six==1.17.0
smmap==5.0.3
soupsieve==2.8.3
SpeechRecognition==3.15.0
streamlit==1.55.0
sympy==1.14.0
tenacity==9.1.4
threadpoolctl==3.6.0
tiktoken==0.12.0
tkinterdnd2==0.4.3
tokenizers==0.22.2
toml==0.10.2
torch==2.10.0
tornado==6.5.5
tqdm==4.67.3
transformers==5.4.0
trimesh==4.11.5
triton==3.6.0
typer==0.24.1
typing-inspection==0.4.2
typing_extensions==4.15.0
tzdata==2025.3
urllib3==2.6.3
watchdog==6.0.0
Werkzeug==3.1.6
```

---

## Gage_env

**Location**: `~/Ethica/modules/gage/gage_env/`  
**Activate**: `source ~/Ethica/modules/gage/gage_env/bin/activate`  
**Purpose**: Gage (Sentinel) — vision worker, Anthropic API access, computer vision, speech, whisper

### Restore
```bash
python3 -m venv ~/Ethica/modules/gage/gage_env
source ~/Ethica/modules/gage/gage_env/bin/activate
pip install -r REQUIREMENTS.md  # use the pinned list below
```

### Pinned Packages
```
altair==6.0.0
annotated-doc==0.0.4
annotated-types==0.7.0
anthropic==0.86.0
anyio==4.12.1
attrs==25.4.0
blinker==1.9.0
cachetools==7.0.5
certifi==2026.2.25
charset-normalizer==3.4.5
click==8.3.1
cuda-bindings==13.2.0
cuda-pathfinder==1.4.2
cuda-toolkit==13.0.2
distro==1.9.0
docstring_parser==0.17.0
filelock==3.25.2
fsspec==2026.2.0
gitdb==4.0.12
GitPython==3.1.46
h11==0.16.0
hf-xet==1.4.0
httpcore==1.0.9
httpx==0.28.1
huggingface_hub==1.6.0
idna==3.11
Jinja2==3.1.6
jiter==0.13.0
joblib==1.5.3
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
llvmlite==0.46.0
markdown-it-py==4.0.0
MarkupSafe==3.0.3
mdurl==0.1.2
more-itertools==10.8.0
mpmath==1.3.0
narwhals==2.18.0
networkx==3.6.1
numba==0.64.0
numpy==2.4.3
nvidia-cublas==13.1.0.3
nvidia-cublas-cu12==12.8.4.1
nvidia-cuda-cupti==13.0.85
nvidia-cuda-cupti-cu12==12.8.90
nvidia-cuda-nvrtc==13.0.88
nvidia-cuda-nvrtc-cu12==12.8.93
nvidia-cuda-runtime==13.0.96
nvidia-cuda-runtime-cu12==12.8.90
nvidia-cudnn-cu12==9.10.2.21
nvidia-cudnn-cu13==9.19.0.56
nvidia-cufft==12.0.0.61
nvidia-cufft-cu12==11.3.3.83
nvidia-cufile==1.15.1.6
nvidia-cufile-cu12==1.13.1.3
nvidia-curand==10.4.0.35
nvidia-curand-cu12==10.3.9.90
nvidia-cusolver==12.0.4.66
nvidia-cusolver-cu12==11.7.3.90
nvidia-cusparse==12.6.3.3
nvidia-cusparse-cu12==12.5.8.93
nvidia-cusparselt-cu12==0.7.1
nvidia-cusparselt-cu13==0.8.0
nvidia-nccl-cu12==2.27.5
nvidia-nccl-cu13==2.28.9
nvidia-nvjitlink==13.0.88
nvidia-nvjitlink-cu12==12.8.93
nvidia-nvshmem-cu12==3.4.5
nvidia-nvshmem-cu13==3.4.5
nvidia-nvtx==13.0.85
nvidia-nvtx-cu12==12.8.90
openai-whisper==20250625
packaging==26.0
pandas==2.3.3
pdf2image==1.17.0
pillow==12.1.1
protobuf==6.33.5
pyarrow==23.0.1
pydantic==2.12.5
pydantic_core==2.41.5
pydeck==0.9.1
pygame==2.6.1
Pygments==2.19.2
pypdf==6.9.2
python-dateutil==2.9.0.post0
pyttsx3==2.99
pytz==2026.1.post1
PyYAML==6.0.3
referencing==0.37.0
regex==2026.2.28
requests==2.32.5
rich==14.3.3
rpds-py==0.30.0
safetensors==0.7.0
scapy==2.7.0
scikit-learn==1.8.0
scipy==1.17.1
shellingham==1.5.4
six==1.17.0
smmap==5.0.3
sniffio==1.3.1
SpeechRecognition==3.15.1
streamlit==1.55.0
sympy==1.14.0
tenacity==9.1.4
threadpoolctl==3.6.0
tiktoken==0.12.0
tokenizers==0.22.2
toml==0.10.2
torch==2.11.0+cpu
tornado==6.5.5
tqdm==4.67.3
transformers==5.3.0
trimesh==4.11.3
triton==3.6.0
typer==0.24.1
typing-inspection==0.4.2
typing_extensions==4.15.0
tzdata==2025.3
urllib3==2.6.3
watchdog==6.0.0
whisper==1.1.10
```

---

## J.A.R.V.I.S. — CVE Database (Sovereign Local)

**Repo**: `https://github.com/Trinity963/cvelistV5.git`  
**Location**: `~/cvelistV5` (outside Ethica dir — config-driven path)  
**Config**: `~/Ethica/config/jarvis_config.json` → `cve_path`

> ⚠️ **This is a large repository.**  
> Transfer size: ~956 MiB | On-disk size: **3.8 GB** | Objects: 1,119,438  
> Plan accordingly on a new machine. A slow connection will take a long time.

### First-time clone
```bash
git clone https://github.com/Trinity963/cvelistV5.git ~/cvelistV5
```

### On restore — if you already have a copy
Do **not** reclone. Just update `jarvis_config.json` to point at your existing copy:
```json
{
  "cve_path": "/path/to/your/cvelistV5"
}
```

### Keep it current
```bash
git -C ~/cvelistV5 pull
```
Or from inside Ethica: `jarvis update`

### J.A.R.V.I.S. pipeline tools (optional —  Easter egg)
```bash
# Go tools
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Python tools
pip install httpx shodan
```

---

## Key Differences

| Package | Ethica_env | Gage_env | Notes |
|---------|-----------|----------|-------|
| `anthropic` | ✗ | `0.86.0` | Gage uses Anthropic API directly |
| `ollama` | `0.6.1` | ✗ | Ethica uses Ollama for local LLM |
| `llama_cpp_python` | `0.3.16` | ✗ | Local inference in Ethica |
| `sentence-transformers` | `5.3.0` | ✗ | Mnemis embeddings in Ethica |
| `tkinterdnd2` | `0.4.3` | ✗ | Canvas drag-and-drop (Ethica UI) |
| `scapy` | `2.7.0` | `2.7.0` | Both — firewall + Gage vision |
| `pqcrypto` | `0.4.0` | ✗ | Post-quantum crypto in Ethica |
| `pyinstaller` | `6.19.0` | ✗ | Packaging in Ethica only |
| `psutil` | `7.2.2` | ✗ | Process management in Ethica |
| `torch` | `2.10.0` (CUDA) | `2.11.0+cpu` | Gage is CPU-only torch |
| `whisper` | ✗ | `1.1.10` | Gage speech recognition |
| `jiter` | ✗ | `0.13.0` | Anthropic SDK dependency |
| `distro` | ✗ | `1.9.0` | Anthropic SDK dependency |
| `cuda-toolkit` | ✗ | `13.0.2` | Gage env CUDA toolkit |

---

*Ethica v0.1 — Session 065* ⟁Σ∿∞
