import os
import logging
import argparse
from typing import List, Optional, Union
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense

def setup_logging(log_level: str = 'INFO') -> None:
    """
    Configure logging for the application.

    Args:
        log_level (str, optional): Logging level. Defaults to 'INFO'.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_discord_logs(file_path: str) -> pd.DataFrame:
    """
    Load Discord chat logs from a CSV or JSON file.

    Args:
        file_path (str): Path to the Discord chat log file.

    Returns:
        pd.DataFrame: DataFrame containing chat messages.
    """
    logging.info(f'Loading chat logs from {file_path}')
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            return pd.read_json(file_path)
        else:
            raise ValueError('Unsupported file format. Use .csv or .json')
    except Exception as e:
        logging.error(f'Error loading chat logs: {e}')
        raise

def preprocess_messages(
    messages: pd.DataFrame, 
    message_column: str = 'content', 
    max_tokens: int = 10000,
    max_sequence_length: int = 50
) -> tuple:
    """
    Preprocess chat messages for model training.

    Args:
        messages (pd.DataFrame): DataFrame containing chat messages.
        message_column (str, optional): Column name for message content. Defaults to 'content'.
        max_tokens (int, optional): Maximum number of tokens to keep. Defaults to 10000.
        max_sequence_length (int, optional): Maximum sequence length for padding. Defaults to 50.

    Returns:
        tuple: Tokenized and padded input and output sequences.
    """
    logging.info('Preprocessing chat messages')
    
    # Clean and prepare messages
    messages[message_column] = messages[message_column].fillna('')
    messages[message_column] = messages[message_column].str.lower()
    
    # Create input and output sequences
    tokenizer = Tokenizer(num_words=max_tokens, oov_token='<OOV>')
    tokenizer.fit_on_texts(messages[message_column])
    
    input_sequences = tokenizer.texts_to_sequences(messages[message_column][:-1])
    output_sequences = tokenizer.texts_to_sequences(messages[message_column][1:])
    
    # Pad sequences
    input_padded = pad_sequences(input_sequences, maxlen=max_sequence_length, padding='pre')
    output_padded = pad_sequences(output_sequences, maxlen=max_sequence_length, padding='pre')
    
    return input_padded, output_padded, tokenizer


def create_chatbot_model(
    vocab_size: int, 
    sequence_length: int,
    embedding_dim: int = 100, 
    rnn_units: int = 256
) -> tf.keras.Model:
    """
    Create a sequential LSTM model for chatbot training.

    Args:
        vocab_size (int): Size of the vocabulary.
        sequence_length (int): Length of input sequences.
        embedding_dim (int, optional): Dimension of embedding layer. Defaults to 100.
        rnn_units (int, optional): Number of RNN units. Defaults to 256.

    Returns:
        tf.keras.Model: Compiled TensorFlow model.
    """
    logging.info('Creating chatbot model architecture')
    model = Sequential([
        Embedding(vocab_size, embedding_dim, input_length=sequence_length),
        LSTM(rnn_units, return_sequences=True),
        Dense(vocab_size, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam', 
        loss='sparse_categorical_crossentropy', 
        metrics=['accuracy']
    )
    
    return model

def train_chatbot_model(
    input_sequences: np.ndarray, 
    output_sequences: np.ndarray,
    model: tf.keras.Model,
    epochs: int = 50,
    batch_size: int = 64
) -> tf.keras.Model:
    """
    Train the chatbot model.

    Args:
        input_sequences (np.ndarray): Preprocessed input sequences.
        output_sequences (np.ndarray): Preprocessed output sequences.
        model (tf.keras.Model): Compiled TensorFlow model.
        epochs (int, optional): Number of training epochs. Defaults to 50.
        batch_size (int, optional): Training batch size. Defaults to 64.

    Returns:
        tf.keras.Model: Trained TensorFlow model.
    """
    logging.info('Training chatbot model')
    
    # Reshape output for sparse categorical crossentropy
    output_sequences = output_sequences.reshape(output_sequences.shape[0], output_sequences.shape[1], 1)
    
    history = model.fit(
        input_sequences, 
        output_sequences,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.2
    )
    
    return model

def main(args: argparse.Namespace) -> None:
    """
    Main function to orchestrate chatbot training process.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    # Setup logging
    setup_logging(args.log_level)
    
    # Load Discord chat logs
    chat_logs = load_discord_logs(args.input_file)
    
    # Preprocess messages
    input_padded, output_padded, tokenizer = preprocess_messages(
        chat_logs, 
        message_column=args.message_column,
        max_tokens=args.max_tokens,
        max_sequence_length=args.max_sequence_length
    )
    
    # Create and train model
    model = create_chatbot_model(
        vocab_size=len(tokenizer.word_index) + 1,
        sequence_length=input_padded.shape[1],
        embedding_dim=args.embedding_dim,
        rnn_units=args.rnn_units
    )
    
    trained_model = train_chatbot_model(
        input_padded, 
        output_padded, 
        model,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    # Save model and tokenizer
    if args.output_model:
        logging.info(f'Saving model to {args.output_model}')
        trained_model.save(args.output_model)
    
    if args.output_tokenizer:
        logging.info(f'Saving tokenizer to {args.output_tokenizer}')
        with open(args.output_tokenizer, 'wb') as handle:
            import pickle
            pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the chatbot trainer.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Train a chatbot model from Discord logs')
    parser.add_argument(
        '-i', '--input-file', 
        required=True, 
        help='Path to Discord chat log file (CSV or JSON)'
    )
    parser.add_argument(
        '-mc', '--message-column', 
        default='content', 
        help='Column name containing message content'
    )
    parser.add_argument(
        '-o', '--output-model', 
        help='Path to save trained model'
    )
    parser.add_argument(
        '-t', '--output-tokenizer', 
        help='Path to save tokenizer'
    )
    parser.add_argument(
        '-l', '--log-level', 
        default='INFO', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level'
    )
    parser.add_argument(
        '--max-tokens', 
        type=int, 
        default=10000, 
        help='Maximum number of tokens to keep'
    )
    parser.add_argument(
        '--max-sequence-length', 
        type=int, 
        default=50, 
        help='Maximum sequence length for padding'
    )
    parser.add_argument(
        '--embedding-dim', 
        type=int, 
        default=100, 
        help='Dimension of embedding layer'
    )
    parser.add_argument(
        '--rnn-units', 
        type=int, 
        default=256, 
        help='Number of RNN units'
    )
    parser.add_argument(
        '--epochs', 
        type=int, 
        default=50, 
        help='Number of training epochs'
    )
    parser.add_argument(
        '--batch-size', 
        type=int, 
        default=64, 
        help='Training batch size'
    )
    
    return parser.parse_args()

if __name__ == '__main__':
    # Parse arguments and run main function
    args = parse_arguments()
    main(args)