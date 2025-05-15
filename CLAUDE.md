# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ppt2desc is a command-line tool that converts PowerPoint presentations into detailed textual descriptions using Vision Language Models (VLMs). It extracts both text content and visual elements from slides to create semantically rich descriptions.

The core workflow is:
1. Convert PowerPoint (PPT/PPTX) files to PDF using LibreOffice
2. Extract individual slide images from the PDF
3. Send each slide image to a Vision Language Model
4. Combine responses into a structured JSON output

## Development Environment

### Dependencies Management

For Python package installation:
```bash
source .venv/bin/activate
uv add <package>
```

For development:
```bash
source .venv/bin/activate
python src/main.py [arguments]
```

## Code Architecture

### Core Components

1. **Converters** (`src/converters/`)
   - `ppt_converter.py`: Converts PPT/PPTX to PDF using local LibreOffice
   - `docker_converter.py`: Converts PPT/PPTX to PDF using a Docker container
   - `pdf_converter.py`: Extracts images from PDFs using PyMuPDF

2. **LLM Clients** (`src/llm/`)
   - `base.py`: Protocol defining the LLM client interface 
   - Specific clients for different providers:
     - `google_unified.py`: Unified client for Gemini API and Vertex AI
     - `openai.py`: Client for OpenAI GPT models
     - `anthropic.py`: Client for Anthropic Claude models
     - `azure.py`: Client for Azure OpenAI deployments
     - `aws.py`: Client for AWS Bedrock models

3. **Main Processing Logic**
   - `processor.py`: Core processing logic for converting files 
   - `main.py`: CLI interface and orchestration

4. **Schema Definitions** (`src/schemas/`)
   - `deck.py`: Pydantic models for structured output

### Key Workflows

1. **Local LibreOffice Workflow**:
   - CLI args → PPT/PPTX file → Local LibreOffice conversion → PDF → Extract images → VLM processing → JSON output

2. **Docker-based LibreOffice Workflow**:
   - CLI args → PPT/PPTX file → Docker API conversion → PDF → Extract images → VLM processing → JSON output

## Usage Examples

Basic usage with Gemini API:
```bash
source .venv/bin/activate
python src/main.py \
    --input_dir /path/to/presentations \
    --output_dir /path/to/output \
    --libreoffice_path /path/to/soffice \
    --client gemini \
    --api_key YOUR_GEMINI_API_KEY
```

Using Docker-based LibreOffice:
```bash
source .venv/bin/activate

# Start Docker container (if not already running)
docker compose up -d

# Run with Docker container endpoint
python src/main.py \
    --input_dir ./presentations \
    --output_dir ./output \
    --libreoffice_url http://localhost:2002 \
    --client vertexai \
    --model gemini-1.5-pro \
    --gcp_project_id my-project-123 \
    --gcp_region us-central1 \
    --gcp_application_credentials ./service-account.json
```