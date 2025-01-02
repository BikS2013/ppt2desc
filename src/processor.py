import time
import logging
import tempfile
from pathlib import Path
from typing import List, Tuple
from tqdm import tqdm

from converters.ppt_converter import convert_pptx_to_pdf
from converters.pdf_converter import convert_pdf_to_images
from llm.gemini import GeminiClient
from schemas.deck import DeckData, SlideData

logger = logging.getLogger(__name__)

def process_single_file(
    ppt_file: Path,
    output_dir: Path,
    libreoffice_path: Path,
    model_instance: GeminiClient,
    rate_limit: int,
    prompt: str
) -> Tuple[Path, List[Path]]:
    """
    Process a single PowerPoint file:
      1) Convert to PDF
      2) Convert PDF to images
      3) Send images to LLM
      4) Save the JSON output
    """
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        try:
            # 1) PPT -> PDF
            pdf_path = convert_pptx_to_pdf(ppt_file, libreoffice_path, temp_dir)
            logger.info(f"Successfully converted {ppt_file.name} to {pdf_path.name}")

            # 2) PDF -> Images
            image_paths = convert_pdf_to_images(pdf_path, temp_dir)
            if not image_paths:
                logger.error(f"No images were generated from {pdf_path.name}")
                return (ppt_file, [])

            # 3) Generate LLM content
            min_interval = 60.0 / rate_limit if rate_limit > 0 else 0
            last_call_time = 0.0

            slides_data = []
            # Sort images by slide number (we know "slide_{page_num + 1}.png" format)
            image_paths.sort(key=lambda p: int(p.stem.split('_')[1]))

            # Initialize tqdm progress bar
            for idx, image_path in enumerate(tqdm(image_paths, desc=f"Processing slides for {ppt_file.name}", unit="slide"), start=1):
                # Rate-limit logic
                if min_interval > 0:
                    current_time = time.time()
                    time_since_last = current_time - last_call_time
                    if time_since_last < min_interval:
                        time.sleep(min_interval - time_since_last)
                    last_call_time = time.time()

                try:
                    response = model_instance.generate(prompt, image_path)
                    slides_data.append(SlideData(
                        number=idx,
                        content=response
                    ))
                except Exception as e:
                    logger.error(f"Error generating content for slide {idx}: {str(e)}")
                    slides_data.append(SlideData(
                        number=idx,
                        content="ERROR: Failed to process slide"
                    ))

            logger.info(f"Successfully converted {ppt_file.name} to {len(slides_data)} slides.")

            # 4) Build pydantic model and save JSON
            deck_data = DeckData(
                deck=ppt_file.name,
                model=model_instance.model_name,
                slides=slides_data
            )
            output_file = output_dir / f"{ppt_file.stem}.json"
            output_file.write_text(deck_data.model_dump_json(indent=2), encoding='utf-8')
            logger.info(f"Output written to {output_file}")

            return (ppt_file, image_paths)

        except Exception as ex:
            logger.error(f"Unexpected error while processing {ppt_file.name}: {str(ex)}")
            return (ppt_file, [])


def process_input_path(
    input_path: Path,
    output_dir: Path,
    libreoffice_path: Path,
    model_instance: GeminiClient,
    rate_limit: int,
    prompt: str
) -> List[Tuple[Path, List[Path]]]:
    """
    Process one or more PPT files from the specified path.
    """
    results = []

    if input_path.is_file():
        if input_path.suffix.lower() in ('.ppt', '.pptx'):
            res = process_single_file(
                input_path,
                output_dir,
                libreoffice_path,
                model_instance,
                rate_limit,
                prompt
            )
            results.append(res)
    else:
        # Process all PPT / PPTX files in directory
        for ppt_file in input_path.glob('*.ppt*'):
            res = process_single_file(
                ppt_file,
                output_dir,
                libreoffice_path,
                model_instance,
                rate_limit,
                prompt
            )
            results.append(res)

    return results
