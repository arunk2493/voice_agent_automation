# voice_agent_automation

# Implementation:
Get and Configure any model API key
Initialize the speak rate limit
AUT url is hard coded
# Voice Agent Creation
  1. Check for the available audio inputs. If any found will use that as audio input if not uses default microphone
  2. Recognizes the voice from the user input and converts it into text
  3. Prompt is created with needed instructions for the model to generate and create test script

# Use of Selenium
  1. Selenium is used for executing the UI automation
  2. Pytest is used to run the selenium test with python
  3. Parses the output and stores the result in CSV
  4. Generates the test scripts automatically and execute the scripts one by one
  5. Once the test completed then the test scripts are stored and shown in html results file
     
# Steps to execute
  1. Set the api key as env variable
  2. Execute below commands
  3. For first time install the dependencies using ```pip install -r requirements.txt```
  4. Execute the script using ```python3 voice_agent_selenium.py```
  5. Provide clear voice input so that the agent listens to the input, generates test scripts and executes it using selenium


<img width="905" alt="Screenshot 2025-03-24 at 1 22 42 AM" src="https://github.com/user-attachments/assets/aa5470e5-b99d-4925-9829-cb65e5162190" />

<img width="1445" alt="Screenshot 2025-03-24 at 1 11 47 AM" src="https://github.com/user-attachments/assets/16488001-274e-4972-8c6a-8ebd65d80e21" />

<img width="1446" alt="Screenshot 2025-03-24 at 1 12 02 AM" src="https://github.com/user-attachments/assets/8706449b-4f0c-43e6-9916-f861b3ab38b4" />