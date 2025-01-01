import argparse
import logging
import glob
import os
import subprocess
import tempfile
import time
import json
import re
import fitz
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image

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

    parser.add_argument(
        "--rate_limit",
        type=int,
        default=60,
        help="Number of API calls allowed per minute (default: 60)"
    )
    
    parser.add_argument(
        "--prompt_path",
        type=str,
        default="src/prompt.txt",
        help="Path to the base prompt file (default: prompt.txt)"
    )

    parser.add_argument(
        "--api_key",
        type=str,
        default=None,
        required=False,
        help="API key for the model. If not provided, will check environment variable."
    )

    if input_args is not None:
        args = parser.parse_args(input_args)
    else:
        args = parser.parse_args()

    return args

def convert_pptx_to_pdf(
    input_file: str, 
    libreoffice_path: str,
    temp_dir: str
) -> Optional[str]:
    """
    Convert a PowerPoint file to PDF using LibreOffice.
    
    Args:
        input_file: Path to the input PowerPoint file
        libreoffice_path: Path to LibreOffice executable
        temp_dir: Temporary directory to store the PDF
    
    Returns:
        Path to the output PDF file if successful, None otherwise
    """
    if not os.path.exists(libreoffice_path):
        logging.error(f"LibreOffice not found at {libreoffice_path}")
        return None

    try:
        # Set up the conversion command
        cmd = [
            libreoffice_path,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', temp_dir,
            input_file
        ]
        
        # Run conversion
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Get the output PDF path
        pdf_name = f"{Path(input_file).stem}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_name)
        
        # Verify the PDF was created
        if os.path.exists(pdf_path):
            return pdf_path
        else:
            logging.error(f"PDF not created at expected path: {pdf_path}")
            logging.error(f"LibreOffice output: {result.stdout}")
            logging.error(f"LibreOffice error: {result.stderr}")
            return None

    except subprocess.CalledProcessError as e:
        logging.error(f"Error converting {input_file}: {e.stderr}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error converting {input_file}: {str(e)}")
        return None

def convert_pdf_to_images(pdf_path: str, temp_dir: str) -> List[str]:
    """
    Convert a PDF file to a series of PNG images.
    
    Args:
        pdf_path: Path to the input PDF file
        temp_dir: Path to temporary directory for storing images
        
    Returns:
        List of paths to generated image files
    """
    target_size = (1920, 1080)
    image_paths = []
    
    try:
        # Create images subdirectory
        images_dir = os.path.join(temp_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        # Open the PDF document
        doc = fitz.open(pdf_path)
        
        # Convert each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Calculate zoom factors
            page_rect = page.rect
            zoom_x = target_size[0] / page_rect.width
            zoom_y = target_size[1] / page_rect.height
            zoom = min(zoom_x, zoom_y)
            
            try:
                # Render page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Create background and paste image
                new_img = Image.new("RGB", target_size, (255, 255, 255))
                paste_x = (target_size[0] - img.width) // 2
                paste_y = (target_size[1] - img.height) // 2
                new_img.paste(img, (paste_x, paste_y))
                
                # Save image
                image_path = os.path.join(images_dir, f"slide_{page_num + 1}.png")
                new_img.save(image_path)
                image_paths.append(image_path)
                
            except Exception as e:
                logging.error(f"Error processing page {page_num + 1}: {str(e)}")
                continue
                
        doc.close()
        return image_paths
        
    except Exception as e:
        logging.error(f"Error converting PDF to images: {str(e)}")
        return []

def process_single_file(
    ppt_file: str,
    output_dir: str,
    libreoffice_path: Optional[str],
    model_instance,
    rate_limit: int,
    prompt_path: str,
    additional_instructions: str
) -> Tuple[str, List[str], tempfile.TemporaryDirectory]:
    """
    Process a single PowerPoint file and convert it to images in temporary storage.
    """
    # Create a temporary directory that will be managed by the caller
    temp_dir_obj = tempfile.TemporaryDirectory()
    temp_dir = temp_dir_obj.name
    
    try:
        # First convert to PDF in the temp directory
        pdf_path = convert_pptx_to_pdf(ppt_file, libreoffice_path, temp_dir)
        if not pdf_path:
            logging.error(f"Failed to convert {ppt_file} to PDF")
            return ppt_file, [], temp_dir_obj
        
        logging.info(f"Successfully created PDF at {pdf_path}")
        
        # Convert PDF to images in the temp directory
        image_paths = convert_pdf_to_images(pdf_path, temp_dir)
        
        if not image_paths:
            logging.error(f"Failed to convert PDF to images for {ppt_file}")
            return ppt_file, [], temp_dir_obj

        # Load prompt
        try:
            with open(prompt_path, 'r') as f:
                base_prompt = f.read().strip()
                if additional_instructions and additional_instructions.lower() != "none provided":
                    prompt = f"{base_prompt}\n\nAdditional instructions to follow:\n{additional_instructions}"
                else:
                    prompt = base_prompt
        except Exception as e:
            logging.error(f"Error reading prompt file: {str(e)}")
            return ppt_file, [], temp_dir_obj

        # Process images with LLM
        min_interval = 60.0 / rate_limit if rate_limit > 0 else 0
        last_call_time = 0

        output_data = {
            "deck": os.path.basename(ppt_file),
            "model": model_instance.model_name,
            "slides": []
        }

        # Sort image paths to ensure correct order
        sorted_paths = sorted(image_paths, key=lambda x: int(re.search(r'slide_(\d+)', x).group(1)))

        for image_path in sorted_paths:
            slide_num = int(re.search(r'slide_(\d+)', image_path).group(1))
            
            # Rate limiting
            if min_interval > 0:
                current_time = time.time()
                time_since_last = current_time - last_call_time
                if time_since_last < min_interval:
                    time.sleep(min_interval - time_since_last)
                last_call_time = time.time()

            try:
                response = model_instance.generate(prompt, image_path)
                content = response.text
            except Exception as e:
                logging.error(f"Error processing slide {slide_num}: {str(e)}")
                content = "ERROR: Failed to process slide"

            output_data["slides"].append({
                "number": slide_num,
                "content": content
            })

        # Save JSON output
        output_file = os.path.join(output_dir, f"{Path(ppt_file).stem}.json")
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        logging.info(f"Successfully processed {ppt_file}")
        return ppt_file, image_paths, temp_dir_obj

    except Exception as e:
        logging.error(f"Error processing {ppt_file}: {str(e)}")
        return ppt_file, [], temp_dir_obj

def process_input_path(
    input_path: str,
    output_dir: str,
    libreoffice_path: Optional[str] = None,
    model_instance = None,
    rate_limit: int = 60,
    prompt_path: str = "prompt.txt",
    additional_instructions: str = None
) -> List[Tuple[str, List[str]]]:
    """Process PowerPoint files and convert them to PDFs and then to images."""
    results = []
    
    if os.path.isfile(input_path):
        if input_path.lower().endswith(('.ppt', '.pptx')):
            results.append(process_single_file(
                input_path, 
                output_dir, 
                libreoffice_path,
                model_instance,
                rate_limit,
                prompt_path,
                additional_instructions
            ))
    else:
        for ppt_file in glob.glob(os.path.join(input_path, '*.ppt*')):
            results.append(process_single_file(
                ppt_file, 
                output_dir, 
                libreoffice_path,
                model_instance,
                rate_limit,
                prompt_path,
                additional_instructions
            ))
    
    return results

def main(args):
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize model instance
    try:
        model_instance = GeminiClient(api_key=args.api_key, model=args.model)
    except Exception as e:
        logging.error(f"Failed to initialize model: {str(e)}")
        return
    
    # Process files
    results = process_input_path(
        args.input_dir,
        args.output_dir,
        args.libreoffice_path,
        model_instance,
        args.rate_limit,
        args.prompt_path,
        args.instructions
    )
    
    # Log results
    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    if successful:
        logging.info(f"Successfully processed {len(successful)} files")
    if failed:
        logging.warning(f"Failed to process {len(failed)} files")

if __name__ == "__main__":
    args = parse_args()
    main(args)