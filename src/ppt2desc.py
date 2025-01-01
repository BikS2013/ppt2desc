import argparse
import logging
import glob
import os
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from models.gemini import GeminiClient

def parse_args(input_args=None):
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        required=True,
        help="Output directory path"
    )

    parser.add_argument(
        "--input_dir",
        type=str,
        default=None,
        required=True,
        help="Path to input directory or file"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="gemini-1.5-flash",
        required=False,
        help="Currently supported models: gemini-1.5-flash, gemini-1.5-pro"
    )

    parser.add_argument(
        "--instructions",
        type=str,
        default="None Provided",
        required=False,
        help="Additional instructions for generation appended to the main prompt"
    )

    parser.add_argument(
        "--libreoffice_path",
        type=str,
        default=None,
        required=False,
        help="Path towards a local installation of Libreoffice"
    )

    if input_args is not None:
        args = parser.parse_args(input_args)
    else:
        args = parser.parse_args()

    return args

def convert_pptx_to_pdf(
    input_file: str, 
    libreoffice_path: str
) -> Optional[str]:
    """
    Convert a PowerPoint file to PDF using LibreOffice.
    
    Args:
        input_file: Path to the input PowerPoint file
        libreoffice_path: Path to LibreOffice executable (optional)
    
    Returns:
        Path to the output PDF file(s) if successful, None otherwise
    """
    
    if not os.path.exists(libreoffice_path):
        logging.error(f"LibreOffice not found at {libreoffice_path}")
        return None

    try:
        # Create temporary directory for conversion
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd = [
                libreoffice_path,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', temp_dir,
                input_file
            ]
            
            # Run conversion
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Get the output PDF name
            pdf_name = f"{Path(input_file).stem}.pdf"
            temp_pdf_path = os.path.join(temp_dir, pdf_name)
            
            return temp_pdf_path

    except subprocess.CalledProcessError as e:
        logging.error(f"Error converting {input_file}: {e.stderr}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error converting {input_file}: {str(e)}")
        return None

def process_input_path(input_path: str, output_dir: str, libreoffice_path: Optional[str] = None) -> list:
    """
    Process either a single PowerPoint file or a directory of PowerPoint files.
    
    Returns:
        List of paths to converted PDF files
    """
    converted_files = []
    
    if os.path.isfile(input_path):
        if input_path.lower().endswith(('.ppt', '.pptx')):
            pdf_path = convert_pptx_to_pdf(input_path, output_dir, libreoffice_path)
            if pdf_path:
                converted_files.append(pdf_path)
    else:
        for pptx_file in glob.glob(os.path.join(input_path, '*.pptx')):
            pdf_path = convert_pptx_to_pdf(pptx_file, output_dir, libreoffice_path)
            if pdf_path:
                converted_files.append(pdf_path)
        for ppt_file in glob.glob(os.path.join(input_path, '*.ppt')):
            pdf_path = convert_pptx_to_pdf(ppt_file, output_dir, libreoffice_path)
            if pdf_path:
                converted_files.append(pdf_path)
    
    return converted_files

def main(args):
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Convert PowerPoints to PDFs
    converted_files = process_input_path(
        args.input_dir,
        args.output_dir,
        args.libreoffice_path
    )
    
    if converted_files:
        logging.info(f"Successfully converted {len(converted_files)} files to PDF")
        for pdf_file in converted_files:
            logging.info(f"Created: {pdf_file}")
    else:
        logging.warning("No PowerPoint files were converted")

if __name__ == "__main__":
    args = parse_args()
    main(args)