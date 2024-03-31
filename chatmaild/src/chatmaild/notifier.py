"""
This modules provides notification machinery for transmitting device tokens to
a central notification server which in turns contacts a phone's notification server
to trigger Delta Chat apps to retrieve messages and provide instant notifications to users.

The Notifier class arranges the queuing of tokens in separate PriorityQueues
from which NotifyThreads take and transmit them via HTTPS
to the `notifications.delta.chat` service
which in turns contacts a phone's providers's notification service
which in turn ewakes up the Delta Chat app on user devices.
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
which device token ultimately goes to which phone-provider notification service.
"""

import time
import logging
from threading import Thread
from queue import PriorityQueue
import requests


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
            self.notification_dir.joinpath(token).write_text(addr)
            self.add_token_for_retry(token)

    def requeue_persistent_pending_tokens(self):
        for token_path in self.notification_dir.iterdir():
            self.add_token_for_retry(token_path.name)

    def add_token_for_retry(self, token, retry_num=0):
        if retry_num >= self.MAX_NUMBER_OF_TRIES:
            return False

        when = time.time()
        if retry_num > 0:
            # backup exponentially with number of retries
            when += pow(self.NOTIFICATION_RETRY_DELAY, retry_num)
        self.retry_queues[retry_num].put((when, token))
        return True

    def start_notification_threads(self, remove_token_from_addr):
        self.requeue_persistent_pending_tokens()
        threads = {}
        for retry_num in range(len(self.retry_queues)):
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
        when, token = self.notifier.retry_queues[self.retry_num].get()
        if when is None:
            return False
        wait_time = when - time.time()
        if wait_time > 0:
            sleep(wait_time)
        self.perform_request_to_notification_server(requests_session, token)
        return True

    def perform_request_to_notification_server(self, requests_session, token):
        token_path = self.notifier.notification_dir.joinpath(token)
        try:
            timeout = self.notifier.CONNECTION_TIMEOUT
            res = requests_session.post(self.notifier.URL, data=token, timeout=timeout)
        except requests.exceptions.RequestException as e:
            res = e
        else:
            if res.status_code in (200, 410):
                if res.status_code == 410:
                    # 410 Gone: means the token is no longer valid.
                    try:
                        addr = token_path.read_text()
                    except FileNotFoundError:
                        logging.warning("no address for token %r:", token)
                        return
                    self.remove_token_from_addr(addr, token)
                token_path.unlink(missing_ok=True)
                return

        logging.warning("Notification request failed: %r", res)
        if not self.notifier.add_token_for_retry(token, retry_num=self.retry_num + 1):
            token_path.unlink(missing_ok=True)
            logging.warning("dropping token after %d tries: %r", self.retry_num, token)
