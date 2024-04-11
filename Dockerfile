FROM public.ecr.aws/lambda/python:3.9

WORKDIR .
COPY packages.txt .
COPY patently.py .
COPY scraping.py .
COPY side_bar.py .

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

CMD ["streamlit", "run", "patently.py"]