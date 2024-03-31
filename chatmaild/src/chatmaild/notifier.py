"""
This modules provides notification machinery for transmitting device tokens to
a central notification server which in turns contacts a phone provider's notification server
to trigger Delta Chat apps to retrieve messages and provide instant notifications to users.

The Notifier class arranges the queuing of tokens in separate PriorityQueues
from which NotifyThreads take and transmit them via HTTPS
to the `notifications.delta.chat` service
which in turn contacts a phone's providers's notification service
which in turn wakes up the Delta Chat app on user devices.
The lack of proper HTTP2-support in Python lets us
use multiple threads and connections to the Rust-implemented `notifications.delta.chat`
which however uses HTTP2 and thus only a single connection to phone-notification providers.

If a token fails to cause a successful notification
it is moved to a retry-number specific PriorityQueue
which handles all tokens that failed a particular number of times
and which are scheduled for retry using exponential back-off timing.
If a token exceeds MAX_NUMBER_OF_TRIES it is dropped with a log warning.

Note that tokens are completely opaque to the notification machinery here
and will in the future be encrypted foreclosing all ability to distinguish
which device token ultimately goes to which phone-provider notification service,
or to understand the relation of "device tokens" and chatmail addresses.
The meaning and format of tokens is basically a matter of Delta-Chat Core and
the `notification.delta.chat` service.
"""

import time
import logging
from uuid import uuid4
from threading import Thread
from pathlib import Path
from queue import PriorityQueue
from dataclasses import dataclass
import requests


@dataclass
class PersistentQueueItem:
    path: Path
    addr: str
    token: str

    def delete(self):
        self.path.unlink(missing_ok=True)

    @classmethod
    def create(cls, queue_dir, addr, token):
        queue_id = uuid4().hex
        path = queue_dir.joinpath(queue_id)
        path.write_text(f"{addr}\n{token}")
        return cls(path, addr, token)

    @classmethod
    def read_from_path(cls, path):
        addr, token = path.read_text().split("\n", maxsplit=1)
        return cls(path, addr, token)


class Notifier:
    URL = "https://notifications.delta.chat/notify"
    CONNECTION_TIMEOUT = 60.0  # seconds until http-request is given up
    NOTIFICATION_RETRY_DELAY = 8.0  # seconds with exponential backoff
    MAX_NUMBER_OF_TRIES = 6
    # exponential backoff means we try for 8^5 seconds, approximately 10 hours

    def __init__(self, notification_dir):
        self.notification_dir = notification_dir
        self.retry_queues = [PriorityQueue() for _ in range(self.MAX_NUMBER_OF_TRIES)]

    def new_message_for_addr(self, addr, metadata):
        for token in metadata.get_tokens_for_addr(addr):
            queue_item = PersistentQueueItem.create(self.notification_dir, addr, token)
            self.queue_for_retry(queue_item)

    def requeue_persistent_queue_items(self):
        for queue_path in self.notification_dir.iterdir():
            queue_item = PersistentQueueItem.read_from_path(queue_path)
            self.queue_for_retry(queue_item)

    def queue_for_retry(self, queue_item, retry_num=0):
        if retry_num >= self.MAX_NUMBER_OF_TRIES:
            queue_item.delete()
            logging.warning("dropping after %d tries: %r", retry_num, queue_item.token)
            return

        when = time.time()
        if retry_num > 0:
            # backup exponentially with number of retries
            when += pow(self.NOTIFICATION_RETRY_DELAY, retry_num)
        self.retry_queues[retry_num].put((when, queue_item))

    def start_notification_threads(self, remove_token_from_addr):
        self.requeue_persistent_queue_items()
        threads = {}
        for retry_num in range(len(self.retry_queues)):
            # use 4 threads for first-try tokens and less for subsequent tries
            num_threads = {0: 4}.get(retry_num, 2)
            threads[retry_num] = []
            for _ in range(num_threads):
                thread = NotifyThread(self, retry_num, remove_token_from_addr)
                threads[retry_num].append(thread)
                thread.start()
        return threads


class NotifyThread(Thread):
    def __init__(self, notifier, retry_num, remove_token_from_addr):
        super().__init__(daemon=True)
        self.notifier = notifier
        self.retry_num = retry_num
        self.remove_token_from_addr = remove_token_from_addr

    def stop(self):
        self.notifier.retry_queues[self.retry_num].put((None, None))

    def run(self):
        requests_session = requests.Session()
        while self.retry_one(requests_session):
            pass

    def retry_one(self, requests_session, sleep=time.sleep):
        when, queue_item = self.notifier.retry_queues[self.retry_num].get()
        if when is None:
            return False
        wait_time = when - time.time()
        if wait_time > 0:
            sleep(wait_time)
        self.perform_request_to_notification_server(requests_session, queue_item)
        return True

    def perform_request_to_notification_server(self, requests_session, queue_item):
        timeout = self.notifier.CONNECTION_TIMEOUT
        token = queue_item.token
        try:
            res = requests_session.post(self.notifier.URL, data=token, timeout=timeout)
        except requests.exceptions.RequestException as e:
            res = e
        else:
            if res.status_code in (200, 410):
                if res.status_code == 410:
                    self.remove_token_from_addr(queue_item.addr, token)
                queue_item.delete()
                return

        logging.warning("Notification request failed: %r", res)
        self.notifier.queue_for_retry(queue_item, retry_num=self.retry_num + 1)
