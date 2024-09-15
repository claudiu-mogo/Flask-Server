""" Threadpool and workers definitions """

from queue import Queue, Empty
from threading import Thread, Event, Lock
import os
import json

class ThreadPool:
    """ ThreadPool of Taskrunners """
    def __init__(self):
        """ Initialize data structures """

        self.no_threads = self.get_no_threads()

        # jobs queue
        self.queue = Queue()
        #list of workers
        self.workers = []
        # counter that retains what job_id to allocate next
        self.id_counter = 0
        # safety measure for incrementing counter
        self.count_lock = Lock()
        # save the statuses for all existent job ids
        self.available_job_ids = {}

        # lock used for merging data ingestors
        self.csv_access_lock = Lock()
        self.ingestor = None

        # event = we can actually do math, the csv is there
        self.merging_csv = Event()

        # event = received graceful_shutdonw, merge threads
        self.shutdown_event = Event()

        # start threads
        for i in range(self.no_threads):
            self.workers.append(TaskRunner(self, i))
            self.workers[i].start()

    def add_job(self, job):
        """ Put a job into the queue, not actually solving it """
        self.queue.put(job)

    def get_no_threads(self):
        """ Get number of threads, don't be confused by no """

        # check env variable
        no_threads = os.environ.get('TP_NUM_OF_THREADS')
        if no_threads is not None:
            return int(no_threads)
        return os.cpu_count()

    def join_workers(self):
        """ After receiving shutdown, we can join the workers """
        for i in range(self.no_threads):
            self.workers[i].join()

class TaskRunner(Thread):
    """ Representation of workers """
    def __init__(self, t_pool, tid):
        """ Initialize Thread ID and get useful data from ThreadPool """

        super().__init__()
        self.t_pool = t_pool
        self.tid = tid

    def write_to_file(self, job_id, content):
        """ Write the result of the computation of job_id """

        directory = os.path.join(os.getcwd(), "results")
        # Create the directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, job_id + ".json")

        # Write content to the file
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(content, file)
        except FileNotFoundError as e:
            print(e)

    def build_answer(self, job, result):
        """ Write to file and mark the job as complete """
        self.write_to_file(job["job_id"], result)
        self.t_pool.available_job_ids[job["job_id"]] = "done"

    def run(self):
        # wait until we are sure that data is there
        self.t_pool.merging_csv.wait()
        while True:
            # Repeat until graceful_shutdown
            if self.t_pool.shutdown_event.is_set() and self.t_pool.queue.empty():
                return
            try:
                # Get pending job
                job = self.t_pool.queue.get(timeout=0.2)
            except Empty:
                continue
            result = {}

            # Execute the job and save the result to disk
            if job["request_type"] == "global_mean_request":
                result = {"global_mean": self.t_pool.ingestor.get_global_mean(job["question"])}
            elif job["request_type"] == "state_mean_request":
                result = self.t_pool.ingestor.get_state_mean(job["question"], job["state"])
                result = {job["state"]: result}
            elif job["request_type"] == "states_mean_request":
                result = self.t_pool.ingestor.get_states_mean(job["question"])
            elif job["request_type"] == "best5_request":
                result = self.t_pool.ingestor.get_best5(job["question"])
            elif job["request_type"] == "worst5_request":
                result = self.t_pool.ingestor.get_worst5(job["question"])
            elif job["request_type"] == "diff_from_mean_request":
                result = self.t_pool.ingestor.get_diff_from_mean(job["question"])
            elif job["request_type"] == "state_diff_from_mean_request":
                result = self.t_pool.ingestor.get_state_diff_from_mean(job["question"], job["state"])
            elif job["request_type"] == "mean_by_category_request":
                result = self.t_pool.ingestor.get_mean_by_category(job["question"])
            elif job["request_type"] == "state_mean_by_category_request":
                result = self.t_pool.ingestor.get_state_mean_by_category(job["question"], job["state"])
            else:
                self.t_pool.available_job_ids[job["job_id"]] = {"ceva" : 5.0}

            self.build_answer(job, result)
            self.t_pool.queue.task_done()
