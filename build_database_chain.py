import shutil
import os
import subprocess

class Handler:
    def __init__(self, next_handler=None):
        self.next_handler = next_handler
    def handle(self, data=None):
        if self.next_handler:
            return self.next_handler.handle(data)
        return data


class FolderHandler(Handler):
    def __init__(self, folder_path, clean=False, next_handler=None):
        super().__init__(next_handler)
        self.folder_path = folder_path
        self.clean = clean

    def handle(self, data=None):
        data_root = os.path.join(os.path.dirname(self.folder_path), '') if self.folder_path.endswith('factory') else self.folder_path
        if self.clean and os.path.exists(data_root):
            print(f"[Step 0] Cleaning folder '{data_root}' (all pipeline outputs)...")
            shutil.rmtree(data_root)
        # Always create both data/ and data/factory/
        os.makedirs(os.path.dirname(self.folder_path), exist_ok=True)
        os.makedirs(self.folder_path, exist_ok=True)
        return super().handle(data)

class ScrapeHandler(Handler):
    def handle(self, data=None):
        print("[Step 1] Running factory scrapers...")
        subprocess.run(["python3", "-m", "scraping.factory.run_scraping_factory"])
        return super().handle(data)

class CleanAndNormalizeHandler(Handler):
    def handle(self, data=None):
        print("[Step 1.5] Cleaning and normalizing data...")
        subprocess.run(["python3", "scraping/clean_and_normalize.py"])
        return super().handle(data)

class MergeHandler(Handler):
    def handle(self, data=None):
        print("[Step 2] Merging files...")
        subprocess.run(["python3", "scraping/merge_files.py"])
        return super().handle(data)

class EntityHandler(Handler):
    def handle(self, data=None):
        print("[Step 3] Extracting entities...")
        subprocess.run(["python3", "nlp_processing/entity_extractor.py"])
        return super().handle(data)

class SentimentHandler(Handler):
    def handle(self, data=None):
        print("[Step 4] Extracting sentiment...")
        subprocess.run(["python3", "nlp_processing/sentiment_extractor.py"])
        return super().handle(data)

class TopicHandler(Handler):
    def handle(self, data=None):
        print("[Step 5] Extracting topics...")
        subprocess.run(["python3", "nlp_processing/topic_extractor.py"])
        return super().handle(data)


def chain(*handlers):
    for i in range(len(handlers) - 1):
        handlers[i].next_handler = handlers[i + 1]
    return handlers[0]


import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the news database pipeline.")
    parser.add_argument('--clean', action='store_true', help='Clean the output folder before building')
    parser.add_argument('--skip-scraping', action='store_true', help='Skip the scraping step (useful if data already exists)')
    args = parser.parse_args()

    output_folder = os.path.join("data", "factory")

    handlers = [FolderHandler(output_folder, clean=args.clean)]

    if not args.skip_scraping:
        handlers.append(ScrapeHandler())
        handlers.append(CleanAndNormalizeHandler())
        handlers.append(MergeHandler())

    handlers.extend([
        EntityHandler(),
        SentimentHandler(),
        TopicHandler()
    ])
    pipeline = chain(*handlers)
    print("Starting database build pipeline...")
    pipeline.handle()
    print("Pipeline finished. Check the data folder for results.")
