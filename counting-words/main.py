import os
import csv
import time
from pathlib import Path
from openai import OpenAI

# Initialize OpenAI client with hardcoded API key
client = OpenAI(api_key="sk-.")

def get_dc_files():
    """Get all Doctrine and Covenants markdown files sorted by section number."""
    dc_path = Path(__file__).parent.parent / "Doctrine and Covenants"
    files = sorted([f for f in dc_path.glob("dc*.md")])
    return files

def count_savior_words(section_number, content):
    """
    Send content to OpenAI API to count words spoken by the Savior.
    Returns tuple of (word_count, confidence_level)
    """
    prompt = f"""You are analyzing Section {section_number} of the Doctrine and Covenants.

Your task is to count ONLY the words spoken directly by Jesus Christ (the Savior) in this section.

Instructions:
1. In the Doctrine and Covenants, the Savior's words are typically indicated by first-person pronouns like "I", "me", "my" when He is speaking
2. Look for phrases like "I the Lord", "thus saith the Lord", "verily I say", etc.
3. Count ALL words that are direct quotations from the Savior
4. Do NOT count:
   - Narrative text
   - Words spoken by other people
   - Verse numbers in markdown like ## 1. as words.
   - Descriptions about the Savior (third person references)

Please analyze the following text and provide:
1. The total word count of ONLY the Savior's direct words
2. Your confidence level as a percentage (0-100) in this count

Section Content:
{content}

Respond in the following format ONLY:
WORD_COUNT: [number]
CONFIDENCE: [percentage without % symbol, e.g., 95]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-4o-mini (note: gpt-5-nano doesn't exist yet)
            messages=[
                {"role": "system", "content": "You are an expert at analyzing religious texts and counting words with precision."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for more consistent results
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse the response
        word_count = None
        confidence = None
        
        for line in response_text.split('\n'):
            if 'WORD_COUNT:' in line:
                try:
                    word_count = int(line.split(':')[1].strip())
                except:
                    pass
            if 'CONFIDENCE:' in line:
                try:
                    confidence = int(line.split(':')[1].strip())
                except:
                    pass
        
        return word_count, confidence
    
    except Exception as e:
        print(f"Error processing section {section_number}: {e}")
        return None, None

def main():
    """Main function to process all D&C files and create output CSV."""
    print("Starting Doctrine and Covenants word count analysis...")
    
    # Get all D&C files
    dc_files = get_dc_files()
    print(f"Found {len(dc_files)} sections to process\n")
    
    # Prepare results list
    results = []
    
    # Process each file
    for idx, file_path in enumerate(dc_files, 1):
        # Extract section number from filename (e.g., dc001.md -> 1)
        section_num = int(file_path.stem.replace('dc', ''))
        
        print(f"Processing Section {section_num} ({idx}/{len(dc_files)})...")
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get word count from OpenAI
        word_count, confidence = count_savior_words(section_num, content)
        
        if word_count is not None:
            results.append({
                'section': section_num,
                'words': word_count,
                'confidence': confidence if confidence else 0
            })
            print(f"  → {word_count} words (confidence: {confidence}%)")
        else:
            print(f"  → Failed to get count")
            results.append({
                'section': section_num,
                'words': 'ERROR',
                'confidence': 0
            })
        
        # Small delay to respect rate limits
        time.sleep(0.5)
        print()
    
    # Write results to CSV
    output_path = Path(__file__).parent / "output.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['section', 'words', 'confidence'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✓ Analysis complete! Results written to {output_path}")
    print(f"  Processed {len(results)} sections")
    
    # Print summary statistics
    successful = sum(1 for r in results if r['words'] != 'ERROR')
    total_words = sum(int(r['words']) for r in results if isinstance(r['words'], int))
    print(f"  Successfully analyzed: {successful}/{len(results)}")
    print(f"  Total words of the Savior: {total_words:,}")

if __name__ == "__main__":
    main()
