import json
import re
import argparse

def clean_text(text):
    """
    Cleans the input text by removing unwanted characters, normalizing whitespace,
    and handling special characters.
    """
    if not isinstance(text, str):
        return text

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove extra whitespace
    text = ' '.join(text.split())

    # Normalize unicode characters
    text = text.encode('ascii', 'ignore').decode('utf-8')

    # Remove non-alphanumeric characters (except for punctuation)
    text = re.sub(r'[^a-zA-Z0-9\s.,;!?\'"]', '', text)

    return text.strip()

def split_content(content, max_length=512):
    """
    Splits the content into smaller chunks if it's too long.
    First, it splits by newlines, then by sentences.
    """
    if not isinstance(content, str) or len(content) <= max_length:
        return [content]

    chunks = []
    # Split by newline characters first
    paragraphs = content.split('\n')
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
        # Then split by sentences
        sentences = re.split(r'(?<=[.!?]) +', paragraph)
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        if current_chunk:
            chunks.append(current_chunk.strip())
            
    return chunks

def process_articles(articles):
    """
    Processes a list of articles, cleaning the title and content.
    """
    processed_articles = []
    for article in articles:
        if 'title' in article:
            article['title'] = clean_text(article['title'])
        if 'content' in article:
            cleaned_content = clean_text(article['content'])
            article['content'] = split_content(cleaned_content)
        processed_articles.append(article)
    return processed_articles

def main():
    parser = argparse.ArgumentParser(description='Clean and normalize article content in JSON files.')
    parser.add_argument('input_file', help='The path to the input JSON file.')
    parser.add_argument('output_file', help='The path to the output JSON file.')
    args = parser.parse_args()

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {args.input_file}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {args.input_file}")
        return

    if 'articles' in data and isinstance(data['articles'], list):
        data['articles'] = process_articles(data['articles'])
    else:
        print("Warning: 'articles' key not found or not a list in the input file.")

    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Successfully cleaned and saved data to {args.output_file}")
    except IOError:
        print(f"Error: Could not write to output file at {args.output_file}")

if __name__ == '__main__':
    main()
