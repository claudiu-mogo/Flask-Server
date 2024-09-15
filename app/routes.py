""" Server architecture """

import json
from flask import request, jsonify
from app import webserver

# Example endpoint definition
@webserver.route('/api/post_endpoint', methods=['POST'])
def post_endpoint():
    """ Demo endpoint """
    if request.method == 'POST':
        # Assuming the request contains JSON data
        data = request.json
        print(f"got data in post {data}")

        # Process the received data
        # For demonstration purposes, just echoing back the received data
        response = {"message": "Received data successfully", "data": data}

        # Sending back a JSON response
        return jsonify(response)
    # Method Not Allowed
    return jsonify({"error": "Method not allowed"}), 405

def merge_ingestor():
    """ At the first GET or POST request, create a field in ThreadPool for the ingestor """
    with webserver.tasks_runner.csv_access_lock:
        if not webserver.tasks_runner.ingestor and webserver.data_ingestor:
            webserver.tasks_runner.ingestor = webserver.data_ingestor
            # Allow the threads to start execution
            webserver.tasks_runner.merging_csv.set()

def generate_job(req):
    """ General method to parse request, create a job and put that job in queue """

    # we previously received shutdown, return that the server is now "closed"
    if webserver.tasks_runner.shutdown_event.is_set():
        return jsonify({"job_id": -1, "reason": "shutdown"})

    # beautify the request type
    request_type = str(req.url_rule).replace('/api/', '') + "_request"

    webserver.logger.info("Received %s POST", request_type)
    # Get request data
    data = req.json

    # check if it is the first request. If so, add the ingestor to threadpool
    merge_ingestor()

    data_dict = {}
    data_dict["request_type"] = request_type
    data_dict["question"] = data["question"]
    if "state" in data.keys():
        data_dict["state"] = data["state"]
    with webserver.tasks_runner.count_lock:
        # Increment job_id counter
        webserver.tasks_runner.id_counter += 1
        job_id = "job_id_" + str(webserver.tasks_runner.id_counter)
        webserver.tasks_runner.available_job_ids[job_id] = "running"
    data_dict["job_id"] = job_id

    # Register job. Don't wait for task to finish
    webserver.tasks_runner.add_job(data_dict)

    webserver.logger.info("Exited %s POST with %s", request_type, str(data_dict))
    # Return associated job_id
    return jsonify({"job_id": job_id, "status": "success"})

@webserver.route('/api/jobs', methods=['GET'])
def get_all_jobs():
    """ Iterate through all entries in the dictionary and retreive job status """

    webserver.logger.info("Received /api/jobs GET")
    merge_ingestor()
    webserver.logger.info("/api/jobs - done")
    data = [{key: value} for key, value in webserver.tasks_runner.available_job_ids.items()]
    return jsonify({"status" : "done", "data" : data})

@webserver.route('/api/num_jobs', methods=['GET'])
def get_num_jobs():
    """ Get how many jobs are currently in running """

    webserver.logger.info("Received /api/num_jobs GET")
    merge_ingestor()
    res = list(filter(lambda x: x == "running", webserver.tasks_runner.available_job_ids.values()))
    webserver.logger.info("/api/num_jobs with %d running - done", len(res))
    return jsonify({"status" : "done", "data" : res})

@webserver.route('/api/graceful_shutdown', methods=['GET'])
def shut():
    """ Set the shutdown event and join workers """

    webserver.tasks_runner.shutdown_event.set()
    webserver.logger.info("Received shutdown GET")
    webserver.tasks_runner.join_workers()
    return jsonify({"status" : "done", "data" : "Done shutdown"})


@webserver.route('/api/get_results/<job_id>', methods=['GET'])
def get_response(job_id):
    """ Get the results of a certain job """

    webserver.logger.info("Received /api/get_results/%s GET", job_id)

    # check if we need to merge ingestor (first request)
    merge_ingestor()
    # Check if job_id is valid

    status = "error"

    # get the existing status from dictionary
    with webserver.tasks_runner.count_lock:
        if job_id in webserver.tasks_runner.available_job_ids:
            status = webserver.tasks_runner.available_job_ids[job_id]

    if status == "error":
        webserver.logger.info("%s - error, invalid job_id", job_id)
        return jsonify({'status': 'error', "reason": "Invalid job_id"})

    if status == "running":
        webserver.logger.info("%s - running", job_id)
        return jsonify({'status': 'running'})

    # the job successfully finished, read the results
    res_file = 'results/' + str(job_id) + '.json'
    with open(res_file, 'r', encoding="utf-8") as f:
        res = json.load(f)

    webserver.logger.info("%s - done", job_id)
    return jsonify({'status': 'done', 'data': res})

@webserver.route('/api/states_mean', methods=['POST'])
def states_mean_request():
    """ Announce to compute Data_Value mean for all the states separately """
    return generate_job(request)

@webserver.route('/api/state_mean', methods=['POST'])
def state_mean_request():
    """ Announce to compute Data_Value mean for only one state """
    return generate_job(request)

@webserver.route('/api/best5', methods=['POST'])
def best5_request():
    """ Announce to compute the best 5 states based only on Data Value for a question """
    return generate_job(request)

@webserver.route('/api/worst5', methods=['POST'])
def worst5_request():
    """ Announce to compute the worst 5 states based only on Data Value for a question """
    return generate_job(request)

@webserver.route('/api/global_mean', methods=['POST'])
def global_mean_request():
    """ Announce to compute Data_Value mean for all the states in a single average """
    return generate_job(request)

@webserver.route('/api/diff_from_mean', methods=['POST'])
def diff_from_mean_request():
    """ Announce to compute difference from mean for all the states separately """
    return generate_job(request)

@webserver.route('/api/state_diff_from_mean', methods=['POST'])
def state_diff_from_mean_request():
    """ Announce to compute difference from mean for only one state """
    return generate_job(request)

@webserver.route('/api/mean_by_category', methods=['POST'])
def mean_by_category_request():
    """ Announce to compute all tuples (state, category, stratification_category) for all """
    return generate_job(request)


@webserver.route('/api/state_mean_by_category', methods=['POST'])
def state_mean_by_category_request():
    """ Announce to compute all tuples (state, category, stratification_category) for a state """
    return generate_job(request)

# You can check localhost in your browser to see what this displays
@webserver.route('/')
@webserver.route('/index')
def index():
    """ Display all available routes on the webpage """
    routes = get_defined_routes()
    msg = "Hello, World!\n Interact with the webserver using one of the defined routes:\n"

    # Display each route as a separate HTML <p> tag
    paragraphs = ""
    for route in routes:
        paragraphs += f"<p>{route}</p>"

    msg += paragraphs
    return msg

def get_defined_routes():
    """ Enumerate all routes """
    routes = []
    for rule in webserver.url_map.iter_rules():
        methods = ', '.join(rule.methods)
        routes.append(f"Endpoint: \"{rule}\" Methods: \"{methods}\"")
    return routes
