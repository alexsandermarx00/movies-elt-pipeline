# ── Stage: runtime ────────────────────────────────────────────────
FROM python:3.10-slim

# Keeps Python output unbuffered so logs reach the container runtime immediately
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first — this layer is cached as long as
# requirements.txt doesn't change, making subsequent builds fast
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source after dependencies to maximise layer cache reuse
COPY scrapy.cfg .
COPY rottentomatoes/ rottentomatoes/

# ENTRYPOINT sets the fixed executable; CMD provides overridable defaults.
# Airflow's DockerOperator can override CMD via `command=` without touching
# the image, e.g.:
#   command: ["rtspider", "-a", "movie=oppenheimer", "-a", "action=score"]
ENTRYPOINT ["scrapy", "crawl"]
CMD ["rtspider"]