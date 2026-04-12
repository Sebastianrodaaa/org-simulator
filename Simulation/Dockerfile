# OrgSim deliberation engine (persona gen + swarm/cascade + streaming)
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY infra ./infra
COPY Backend/output ./Backend/output
COPY Simulation ./Simulation

ENV PYTHONPATH=/app/Simulation
ENV ORGSIM_CONFIG=/app/infra/config.yaml
# Inside Docker network — override on host with OLLAMA_HOST=http://127.0.0.1:11434
ENV OLLAMA_HOST=http://ollama:11434
ENV TYPEDB_URI=typedb:1729
ENV LLM_MODEL_NAME=qwen2.5:14b

EXPOSE 8001
WORKDIR /app/Simulation
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
