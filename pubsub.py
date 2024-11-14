from queue import Queue
import threading
import time

# Initialize a queue for Pub/Sub messages
message_queue = Queue()

def publish_message(message):
    """Publish a message to the message queue."""
    message_queue.put(message)
    print(f"Published message: {message}")

def subscribe_to_messages(process_message):
    """Subscribe to messages in the queue and process them as they arrive."""
    while True:
        message = message_queue.get()  # Get the message from the queue
        if message is None:
            break  # End the thread if a None message is sent (for cleanup)
        process_message(message)
        message_queue.task_done()

def start_subscription(process_message):
    """Start a new thread to listen for messages and process them."""
    subscriber_thread = threading.Thread(target=subscribe_to_messages, args=(process_message,))
    subscriber_thread.daemon = True  # Daemonize thread so it closes with the main program
    subscriber_thread.start()
    return subscriber_thread
