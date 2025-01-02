<img src="ppt2desc_icon.png" width=250>

# ppt2desc

Convert PowerPoint presentations into semantically rich text using Vision Language Models (vLLMs).

## Overview

ppt2desc is a command-line tool that converts PowerPoint presentations into detailed textual descriptions. PowerPoint presentations are an inherently visual medium that often convey complex ideas through a combination of text, graphics, charts, and other visual layouts. This tool uses vision language models to not only transcribe the textual content but also interpret and describe the visual elements and their relationships, capturing the full semantic meaning of each slide in a machine-readable format.

## Features

- Convert PPT/PPTX files to semantic descriptions
- Process individual files or entire directories
- Support for visual elements interpretation (charts, graphs, figures)
- Rate limiting for API calls
- Customizable prompts and instructions
- JSON output format for easy integration

**Current Model Provider Support**
- Gemini models via Gemini API
- Google Cloud Platform Model Garden via Vertex AI Service Accounts
- *WIP: OpenAI, Claude, Azure, AWS*

## Prerequisites

- Python 3.9 or higher
- LibreOffice (for PPT/PPTX to PDF conversion)
- vLLM API credentials

## Installation

1. Installing LibreOffice

LibreOffice is a critical dependency for this tool as it handles the headless conversion of PowerPoint files to PDF format

**Ubuntu/Debian:**
```bash
sudo apt install libreoffice
```

**macOS:**
```bash
brew install libreoffice
```

**Windows:**
Build from the installer at [LibreOffice's Official Website](https://www.libreoffice.org/download/download/)

2. Clone the repository:
```bash
git clone https://github.com/yourusername/ppt2desc.git
cd ppt2desc
```

3. Create and activate a virtual environment:
```bash
python -m venv ppt2desc_venv
source ppt2desc_venv/bin/activate  # On Windows: ppt2desc_venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage with Gemini API:
```bash
python src/main.py \
    --input_dir /path/to/presentations \
    --output_dir /path/to/output \
    --libreoffice_path ./soffice \
    --client gemini \
    --api_key YOUR_GEMINI_API_KEY
```

### Command Line Arguments

General Arguments:
- `--input_dir`: Path to input directory or PPT file (required)
- `--output_dir`: Output directory path (required)
- `--client`: LLM client to use: 'gemini' or 'vertexai' (default: "gemini")
- `--model`: Model to use (default: "gemini-1.5-flash")
- `--instructions`: Additional instructions for the model
- `--libreoffice_path`: Path to LibreOffice installation
- `--rate_limit`: API calls per minute (default: 60)
- `--prompt_path`: Custom prompt file path
- `--api_key`: Model Provider API key (if not set via environment variable)

Vertex AI-specific Arguments:
- `--gcp_project_id`: GCP project ID for Vertex AI service account
- `--gcp_region`: GCP region for Vertex AI service (e.g., us-central1)
- `--gcp_application_credentials`: Path to GCP service account JSON credentials file

### Example Commands

Using Gemini API:
```bash
python src/main.py \
    --input_dir ./presentations \
    --output_dir ./output \
    --libreoffice_path ./soffice \
    --client gemini \
    --model gemini-1.5-pro \
    --rate_limit 30 \
    --instructions "Focus on extracting numerical data from charts and graphs"
```

Using Vertex AI:
```bash
python src/main.py \
    --input_dir ./presentations \
    --output_dir ./output \
    --client vertexai \
    --libreoffice_path ./soffice \
    --gcp_project_id my-project-123 \
    --gcp_region us-central1 \
    --gcp_application_credentials ./service-account.json \
    --model gemini-1.5-pro \
    --instructions "Extract detailed information from technical diagrams"
```

## Output Format

The tool generates JSON files with the following structure:

```json
{
  "deck": "presentation.pptx",
  "model": "model-name",
  "slides": [
    {
      "number": 1,
      "content": "Detailed description of slide content..."
    },
    // ... more slides
  ]
}
```

## Advanced Usage

### Custom Prompts

You can modify the base prompt by editing `src/prompt.txt` or providing additional instructions via the command line:

```bash
python src/main.py \
    --input_dir ./presentations \
    --output_dir ./output \
    --instructions "Include mathematical equations and formulas in LaTeX format"
```

### Authentication

For Gemini API:
- Set your API key via the `--api_key` argument or through an environment variable

For Vertex AI:
1. Create a service account in your GCP project
2. Grant necessary permissions (typically, "Vertex AI User" role)
3. Download the service account JSON key file
4. Provide the credentials file path via `--gcp_application_credentials`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [LibreOffice](https://www.libreoffice.org/) for PPT/PPTX conversion
- [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/) for PDF processing