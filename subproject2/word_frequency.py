# Import Libraries
import pandas as pd
import re
from collections import Counter
from pathlib import Path
import matplotlib.pyplot as plt
import os
import sys
from typing import Dict, List, Union
import locale
import io
import codecs
from difflib import SequenceMatcher

# Set up console encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class WordFrequencyAnalyzer:
    def __init__(self):
        self.df = None
        self.word_counts = None
        self.total_words = 0
        # Set default output directory path, can be overridden
        self.output_dir = 'output'
        # Common word variations to normalize
        self.word_variations = {
            'קאשבק': ['קאש בק', 'קש בק', 'קשבק', 'cashback', 'cash back'],
            'כרטיס': ['כרטיס אשראי', 'הכרטיס'],
            'הטבות': ['הטבה'],
            'נקודות': ['נקודת'],
            'קניות': ['קנייה', 'קניה'],
        }
        # Create reverse mapping for quick lookup
        self.word_mapping = {}
        for main_word, variations in self.word_variations.items():
            for var in variations:
                self.word_mapping[var.lower()] = main_word

    def get_similarity_ratio(self, a: str, b: str) -> float:
        """Calculate similarity ratio between two strings."""
        return SequenceMatcher(None, a, b).ratio()

    def combine_similar_words(self, similarity_threshold: float = 0.85) -> None:
        """Combine words that are similar above the threshold."""
        if self.df is None or len(self.df) == 0:
            return

        # Sort by frequency to prioritize more frequent words
        self.df = self.df.sort_values('frequency', ascending=False)
        
        # Create a new DataFrame for the combined results
        new_rows = []
        skip_words = set()

        for i, row in self.df.iterrows():
            if row['word'] in skip_words:
                continue

            base_word = row['word']
            total_freq = row['frequency']
            similar_words = []

            # Compare with all other words
            for j, other_row in self.df.iterrows():
                if i != j and other_row['word'] not in skip_words:
                    other_word = other_row['word']
                    
                    # Check if one word is a prefix of the other
                    is_prefix = other_word.startswith(base_word) or base_word.startswith(other_word)
                    
                    # Calculate similarity only if they share a prefix or are very similar
                    if is_prefix or self.get_similarity_ratio(base_word, other_word) > similarity_threshold:
                        total_freq += other_row['frequency']
                        similar_words.append(other_word)
                        skip_words.add(other_word)

            if similar_words:
                print(f"\nCombined words: {base_word} + {similar_words}")
                
            new_rows.append({
                'word': base_word,
                'frequency': total_freq,
                'percentage': 0  # We'll calculate this later
            })

        # Create new DataFrame and recalculate percentages
        self.df = pd.DataFrame(new_rows)
        total_freq = self.df['frequency'].sum()
        self.df['percentage'] = (self.df['frequency'] / total_freq * 100).round(2)
        self.df = self.df.sort_values('frequency', ascending=False)
        
    def normalize_word(self, word: str) -> str:
        """Normalize word variations to their standard form."""
        word = word.lower()
        return self.word_mapping.get(word, word)
    
    def split_hebrew_words(self, text: str) -> List[str]:
        """Split potentially joined Hebrew words using common patterns."""
        # Common Hebrew word endings to help with splitting
        endings = ['ות', 'ים', 'את', 'תי', 'נו', 'כם', 'הם', 'תם', 'יה']
        
        # First split by common separators
        words = []
        for part in re.split('[;,.\s]+', text):
            if not part:
                continue
            
            # Try to split joined words
            current_word = ""
            for char in part:
                current_word += char
                # If we have a potential word ending, check if the rest is a valid word
                for ending in endings:
                    if current_word.endswith(ending) and len(current_word) > len(ending):
                        rest = part[len(current_word):]
                        if len(rest) > 1:  # Only split if remaining part is long enough
                            words.append(current_word)
                            current_word = ""
                            break
            
            if current_word:
                words.append(current_word)
        
        return words
        
    def clean_text(self, text: str) -> str:
        """Clean text by removing special characters and extra spaces."""
        # Remove punctuation but keep Hebrew and English letters
        text = re.sub(r'[^\w\s\u0590-\u05FF]', ' ', text)
        # Convert multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()
    
    def get_words(self, text: str) -> List[str]:
        """Split text into words, handling both English and Hebrew."""
        # First clean the text
        cleaned_text = self.clean_text(text)
        
        # Split potentially joined words
        words = self.split_hebrew_words(cleaned_text)
        
        # Filter and normalize words
        normalized_words = []
        for word in words:
            if len(word) > 1:  # Skip single characters
                normalized_word = self.normalize_word(word)
                normalized_words.append(normalized_word)
        
        return normalized_words
    
    def analyze_text(self, text: str) -> None:
        """Analyze the text and compute word frequencies."""
        try:
            # Input validation
            if not text or not isinstance(text, str):
                raise ValueError("Input must be a non-empty string")
            
            # Handle empty text
            if text.strip() == "":
                self.word_counts = Counter()
                self.total_words = 0
                self.df = pd.DataFrame(columns=['word', 'frequency', 'percentage'])
                return
                
            # Split text into words
            words = re.findall(r'\b\w+\b', text.lower())
            
            # If no words found, create empty results
            if not words:
                self.word_counts = Counter()
                self.total_words = 0
                self.df = pd.DataFrame(columns=['word', 'frequency', 'percentage'])
                return
            
            # Normalize word variations
            normalized_words = [self.normalize_word(word) for word in words]
            
            # Count word frequencies
            self.word_counts = Counter(normalized_words)
            self.total_words = sum(self.word_counts.values())
            
            # Create DataFrame
            word_freq = [(word, int(count)) for word, count in self.word_counts.most_common()]  # Convert to int
            
            # If no words after processing, create empty DataFrame
            if not word_freq:
                self.df = pd.DataFrame(columns=['word', 'frequency', 'percentage'])
                return
                
            self.df = pd.DataFrame(word_freq, columns=['word', 'frequency'])
            
            # Calculate percentages
            self.df['percentage'] = (self.df['frequency'] / self.total_words * 100).round(2)
            
            # Convert frequency to standard Python int
            self.df['frequency'] = self.df['frequency'].astype(int)
            
            # Combine similar words only if we have words
            if len(self.df) > 0:
                self.combine_similar_words()
            
            # Sort by frequency
            self.df = self.df.sort_values('frequency', ascending=False).reset_index(drop=True)
            
        except Exception as e:
            print(f"Error in analyze_text: {str(e)}")
            # Create empty results on error
            self.word_counts = Counter()
            self.total_words = 0
            self.df = pd.DataFrame(columns=['word', 'frequency', 'percentage'])
    
    def save_results(self) -> None:
        """Save analysis results to files."""
        try:
            # Ensure output directory exists
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Handle case where no data is available
            if self.df is None or len(self.df) == 0:
                # Create empty CSV
                empty_df = pd.DataFrame(columns=['word', 'frequency', 'percentage'])
                empty_df.to_csv(os.path.join(self.output_dir, 'word_frequencies.csv'), index=False, encoding='utf-8')
                
                # Create empty plot
                plt.figure(figsize=(12, 6))
                plt.title('No Words Found')
                plt.xlabel('Words')
                plt.ylabel('Frequency')
                plt.text(0.5, 0.5, 'No words found in the provided text', 
                         horizontalalignment='center', verticalalignment='center',
                         transform=plt.gca().transAxes, fontsize=14)
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'word_frequencies_plot.png'), dpi=300, bbox_inches='tight')
                plt.close()
                return
            
            # Save CSV
            self.df.to_csv(os.path.join(self.output_dir, 'word_frequencies.csv'), index=False, encoding='utf-8')
            
            # Create plot
            plt.figure(figsize=(12, 6))
            
            # Plot top 10 words (or fewer if less available)
            top_n = min(10, len(self.df))
            if top_n > 0:
                top_words = self.df.head(top_n)
                bars = plt.bar(top_words['word'], top_words['frequency'])
                
                # Customize plot
                plt.title('Most Frequent Words')
                plt.xlabel('Words')
                plt.ylabel('Frequency')
                plt.xticks(rotation=45, ha='right')
                
                # Add value labels on top of bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}',
                            ha='center', va='bottom')
            else:
                # No words to plot
                plt.title('No Words Found')
                plt.text(0.5, 0.5, 'No words found in the provided text', 
                         horizontalalignment='center', verticalalignment='center',
                         transform=plt.gca().transAxes, fontsize=14)
            
            # Adjust layout and save
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'word_frequencies_plot.png'), dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"Error in save_results: {str(e)}")
            # Create a minimal plot on error
            try:
                plt.figure(figsize=(12, 6))
                plt.title('Error Processing Text')
                plt.text(0.5, 0.5, f'Error: {str(e)}', 
                         horizontalalignment='center', verticalalignment='center',
                         transform=plt.gca().transAxes, fontsize=14)
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'word_frequencies_plot.png'), dpi=300, bbox_inches='tight')
                plt.close()
            except:
                pass

    def print_summary(self) -> None:
        """Print analysis summary."""
        if self.df is None:
            raise ValueError("No analysis results available. Run analyze_text first.")
        
        print("\nAnalysis Summary:")
        print(f"Total words: {self.total_words}")
        print(f"Unique words: {len(self.word_counts)}")
        print("\nTop 10 most frequent words:")
        
        # Format DataFrame for display
        pd.set_option('display.unicode.east_asian_width', True)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        print(self.df.head(10).to_string(index=False))

    def get_top_words(self, n=10) -> list:
        """Get the top n most frequent words."""
        if self.df is None:
            raise ValueError("No analysis results available. Run analyze_text first.")
        
        top_n = self.df.head(n)
        return top_n.to_dict('records')
    
    def get_total_words(self) -> int:
        """Get the total number of words."""
        return self.total_words
    
    def get_unique_words(self) -> int:
        """Get the number of unique words."""
        if self.word_counts is None:
            raise ValueError("No analysis results available. Run analyze_text first.")
        
        return len(self.word_counts)

def main():
    # Configure UTF-8 output
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    if len(sys.argv) != 2:
        print("\nUsage: python word_frequency.py <text_file>")
        print("The text file should be UTF-8 encoded and can contain English or Hebrew text.")
        sys.exit(1)
    
    try:
        # Read input file
        input_file = sys.argv[1]
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Create analyzer and process text
        analyzer = WordFrequencyAnalyzer()
        analyzer.analyze_text(text)
        
        # Save results and print summary
        analyzer.save_results()
        analyzer.print_summary()
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
