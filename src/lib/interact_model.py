import argparse
import logging
from typing import Union, Optional
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TextGenerator:
    """
    A class to handle text generation using a pre-trained Keras model.

    Attributes:
        model (keras.Model): Loaded Keras model for text generation
        tokenizer (Tokenizer): Tokenizer used for text preprocessing
        max_sequence_len (int): Maximum sequence length for input
    """

    def __init__(
        self, 
        model_path: str, 
        tokenizer_path: Optional[str] = None
    ):
        """
        Initialize the TextGenerator with a model and optional tokenizer.

        Args:
            model_path (str): Path to the saved Keras model
            tokenizer_path (Optional[str]): Path to the saved tokenizer
        """
        try:
            # Load model
            self.model = keras.models.load_model(model_path)
            logger.info(f"Model successfully loaded from {model_path}")

            # Load or create tokenizer
            if tokenizer_path:
                import pickle
                with open(tokenizer_path, 'rb') as handle:
                    self.tokenizer = pickle.load(handle)
            else:
                logger.warning("No tokenizer provided. Generating a default tokenizer may not work correctly.")
                self.tokenizer = Tokenizer()

            # Determine max sequence length (might need adjustment based on your model)
            self.max_sequence_len = self.model.input_shape[1]
            logger.info(f"Max sequence length: {self.max_sequence_len}")

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            raise

    def preprocess_text(self, text: str) -> np.ndarray:
        """
        Preprocess input text into a model-compatible format.

        Args:
            text (str): Input text to be preprocessed

        Returns:
            np.ndarray: Preprocessed and padded sequence
        """
        try:
            # Tokenize the input text
            sequence = self.tokenizer.texts_to_sequences([text])
            
            # Pad the sequence
            padded_sequence = pad_sequences(
                sequence, 
                maxlen=self.max_sequence_len, 
                padding='pre', 
                truncating='pre'
            )
            
            return padded_sequence
        except Exception as e:
            logger.error(f"Text preprocessing error: {e}")
            raise

    def generate_response(
        self, 
        input_text: str, 
        max_response_length: int = 50
    ) -> str:
        """
        Generate a text response based on the input text.

        Args:
            input_text (str): Input text to generate a response for
            max_response_length (int): Maximum length of the generated response

        Returns:
            str: Generated text response
        """
        try:
            # Preprocess input text
            preprocessed_input = self.preprocess_text(input_text)
            
            # Generate response tokens
            generated_tokens = []
            for _ in range(max_response_length):
                # Predict the next token
                predicted_probs = self.model.predict(preprocessed_input, verbose=0)[0]
                
                # Sample from the probability distribution
                predicted_token = np.random.choice(
                    len(predicted_probs), 
                    p=predicted_probs
                )
                
                # Add to generated tokens
                generated_tokens.append(predicted_token)
                
                # Update input sequence
                preprocessed_input = pad_sequences(
                    [preprocessed_input[0][1:] + [predicted_token]], 
                    maxlen=self.max_sequence_len, 
                    padding='pre', 
                    truncating='pre'
                )
                
                # Stop if end token is generated
                if predicted_token == self.tokenizer.word_index.get('<END>', None):
                    break
            
            # Convert tokens back to text
            response = self.tokenizer.sequences_to_texts([generated_tokens])[0]
            
            logger.info("Response generated successfully")
            return response
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            raise

def main():
    """
    Main function to parse arguments and demonstrate text generation.
    """
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Text Generation Model Inference Script")
    parser.add_argument(
        'model_path', 
        type=str, 
        help='Path to the saved Keras model'
    )
    parser.add_argument(
        '--tokenizer', 
        type=str, 
        help='Path to the saved tokenizer (optional)'
    )
    parser.add_argument(
        '--input', 
        type=str, 
        default="Hello",
        help='Input text for generation (default: "Hello")'
    )
    parser.add_argument(
        '--max_length', 
        type=int, 
        default=50, 
        help='Maximum length of generated response'
    )
    args = parser.parse_args()

    try:
        # Initialize text generator
        text_generator = TextGenerator(
            model_path=args.model_path, 
            tokenizer_path=args.tokenizer
        )

        # Generate response
        response = text_generator.generate_response(
            input_text=args.input, 
            max_response_length=args.max_length
        )
        
        print(f"Input: {args.input}")
        print(f"Generated Response: {response}")

    except Exception as e:
        logger.error(f"Script execution failed: {e}")

if __name__ == "__main__":
    main()