# Generic Consumer

A flexible Python library for implementing consumer patterns with a focus on payload processing and queue management.

## Overview

Generic Consumer provides a framework for creating consumer classes that can process data payloads from various sources. It supports both synchronous and asynchronous processing with features like:

- Prioritized execution order
- Payload preprocessing
- Conditional activation
- Nested consumer hierarchies
- Robust error handling
- Customizable logging

## Installation

### Using pip

```bash
pip install generic-consumer
```

## Quick Start

```python
from generic_consumer import GenericConsumer

class MyConsumer(GenericConsumer):
    # Set the queue this consumer responds to
    @classmethod
    def queue_name(cls):
        return "my_queue"
    
    # Define where to get payloads from
    def get_payloads(self):
        return [1, 2, 3, 4, 5]
    
    # Process a single payload
    def process_one(self, payload):
        print(f"Processing: {payload}")
        
# Run all consumers for a queue
GenericConsumer.start("my_queue")
```

## Key Features

### Consumer Configuration

- **queue_name**: Define which queue a consumer belongs to
- **priority_number**: Set execution priority (lower numbers run first)
- **condition**: Determine whether a consumer should run based on runtime conditions
- **enabled**: Toggle consumer activation
- **process_empty_payloads**: Handle cases where no payloads are available
- **passive**: Create consumers that monitor but don't process (useful for logging)

### Processing Pipeline

1. **get_payloads**: Retrieve data to be processed
2. **payload_preprocessors**: Transform payloads before processing
3. **process**: Handle batch processing of all payloads
4. **process_one**: Process individual payloads

### Utility Methods

- **start_all/start**: Run all consumers for a given queue
- **print_available_consumers**: Display all registered consumers and their configurations
- **run**: Execute a specific consumer
- **run_all**: Execute all consumers

## Advanced Usage

### Passive Consumers

Use `PassiveConsumer` for monitoring or logging without modifying data:

```python
from generic_consumer import PassiveConsumer

class LoggingConsumer(PassiveConsumer):
    @classmethod
    def queue_name(cls):
        return "my_queue"
    
    def process(self, payloads):
        print(f"Observed {len(payloads)} items")
```
