# Flask-Server

A server implementation that responds to a request regarding data from a .csv file

Project goal: implementing a Python server that will handle a series of requests starting from a dataset in _csv_ (comma-separated values) format.
The server will provide statistics based on the data from the csv.

===== Implementation Details =====

The developed server application is multi-threaded.
When the server starts, it must load the csv file and extract the information from it so that it can calculate the statistics requested per request.

Since processing data from the csv can take more time, the model implemented by the server will be as follows:

- An endpoint (e.g., '/api/states_mean') that receives the request and returns a **job_id** to the client (e.g., "job_id_1", "job_id_2", ..., "job_id_n").
- The endpoint '/api/get_results/job_id' which will check if the job_id is valid, if the calculation result is ready or not, and will return an appropriate response.

=== Request Mechanics ===

Associate a job_id with the request, put the job (closure that encapsulates the unit of work) into a job queue that is processed by a **Thread pool**, increment the internal job_id, and return the associated job_id to the client.

A thread will take a job from the job queue, perform the associated operation (captured by the closure), and write the calculation result into a file named after the job_id in the **results/** directory.

## General approach:

- Parse the CSV using the DataIngestor, which also provides the methods for various calculations.

- Store data after parsing the csv:

  - Large dictionary: {question : small_dictionary}
  - Small dictionary: {stat : list of tuples}
  - Tuple: (data_value, stratification1, stratification category)

- Create a ThreadPool from scratch whose main elements are a job queue, represented by a Queue module, a list of Workers (Task_runner), and a dictionary self.available_job_ids in which the entries are in the form {"job_id_X" : status}, where the status is initially running and changes to done when the job is completed. If a job-id is not in the dictionary, then it never existed, so we consider the status as an error.

- Job representation: a dictionary containing the following keys:

  - question -> the question itself
  - request_type -> which calculation method to be called
  - state -> the state in question (may be missing)
  - job_id -> the associated job-id

- A thread waits at get and takes the next task from the queue, calculates the output, writes it to a file, then marks the task as done in the dictionary. In exactly this order. So, if we see the status "done" in the dictionary, we are sure that we will also have the answer in results/job_id_x. We don't store the result in RAM to avoid the case where the output is very large; we only save the statuses in RAM.

* Relationship between ingestor and threadpool: On the first request, no matter what it is, it will enter the if statement in the "merge_ingestor" method from routes.py and trigger an event so that threads now have access to the data. Initially, in the thread run, these are in wait. They can now process jobs from the queue.

## Testing (3 terminals):

- One with the server itself.
- One where I ran a script that launches "make run_tests" a few dozen times in the background (to do heavy-duty work and also catch tasks running):
  ```bash
  for i in {1..20}
  do
      make run_tests &
  done
  ```
- One where I spam curl URL for the GET requests I created and that are not tested by the checker, with output redirected to another file. They work as they should; I even find 2 jobs running at a time for many things in the background, which is good.

## Difficulties encountered & Interesting things discovered:

Due to or thanks to the fact that the get on the queue is blocking (it's good that it's synchronized at least), when we shut down the server, those threads will eventually hang in the wait at get. That's why I chose the solution to use get with a 0.2-second timeout to prevent them from getting stuck and to be able to join them. I tested several options, including the get_no_wait variant, but this would have done too much busy waiting on the condition from while True. Therefore, I came to this compromise measure. To get the maximum score (or just if I didn't want to join the threads), it was enough to use a simple blocking get.

I copied my entire ingestor into the unittests directory to test the calculation methods; otherwise, I would have had to call something from the app, meaning I had to go through init, so start the server. The unittesting part was interesting nonetheless. I made my own csv!

Also, the logger (which apparently shows errors in webserver.log) and the web server are created and linked in init; I rely on the fact that they don't count as global variables.

## Resources used:

https://ocw.cs.pub.ro/courses/asc/laboratoare/03
https://docs.python.org/3/library/queue.html
https://stackoverflow.com/questions/44106283/python-multiprocessing-queue-get-timeout-despite-full-queue
https://youtu.be/mqhxxeeTbu0?si=9QdtlKpbOVPexKD6
https://youtu.be/9MHYHgh4jYc?si=6h18GQaUonZcwY0A
