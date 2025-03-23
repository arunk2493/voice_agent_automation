import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import subprocess
import re
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pytest

# Configure Gemini AI 🤖✨
genai.configure(api_key="AIzaSyDd2LxbeMfsqVnAXFJCXXljGh8SI2iY55s")

# Initialize text-to-speech engine 🎙️
engine = pyttsx3.init()
engine.setProperty("rate", 150)  # Speech rate 🎶

# Hardcoded Test URL 🌐
TEST_URL = "https://www.saucedemo.com/"
GENERATED_TESTS_FILE = "generated_tests.py"  # Path to generated test file

# Function to recognize voice input 🎤
def get_audio_source():
    mic_list = sr.Microphone.list_microphone_names()
    print("Available Audio Devices:")
    for i, mic in enumerate(mic_list):
        print(f"{i}: {mic}")
    preferred_devices = ["Bluetooth", "Headset", "Wireless"]
    for i, mic in enumerate(mic_list):
        if any(device in mic for device in preferred_devices):
            print(f"Using preferred audio device: {mic}")
            return sr.Microphone(device_index=i)
    print("No preferred audio device found, using default microphone.")
    return sr.Microphone()

def recognize_voice():
    recognizer = sr.Recognizer()
    with get_audio_source() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        audio = recognizer.listen(source)
    try:
        print("Recognizing speech...")
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand the audio.")
        return None
    except sr.RequestError:
        print("Error with the speech recognition service.")
        return None


# Function to speak response 🎙️
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to generate Selenium test cases dynamically ⚡
def get_ai_response(test_scenario):
    try:
        model = genai.GenerativeModel("models/gemini-1.5-pro")
        prompt = f"""
        Generate Selenium test cases in Python for the following test scenario: "{test_scenario}".

        - Include positive, negative, and edge cases.
        - Use Selenium with Python.
        - Use `By.XPATH`, `By.CSS_SELECTOR`, or `By.NAME` (NO hardcoded IDs).
        - Wrap tests inside a Pytest function with assertions.
        - Use `WebDriverWait` for element interactions.
        - Launch Chrome browser and open: {TEST_URL}.
        - Return only valid Python code, NO explanations or comments.
        - Quit the driver once the test steps are completed for each test case
        - Run test cases in parallel
        - Add proper wait time between the steps and execute the steps
        - Add only the automation code to {GENERATED_TESTS_FILE} file. Incase of any text add as comments
        - Parameterize test cases which needs multiple data like login scenario
        - Do not add any text values or sentences or command in {GENERATED_TESTS_FILE} file.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ Error in AI response: {e}")
        return None

# Function to clean AI-generated text ✂️
def clean_generated_code(code):
    code = re.sub(r"```python", "", code)  
    code = re.sub(r"```", "", code)  
    code = re.sub(r"\*\*(.*?)\*\*", r"\1", code)  
    code = re.sub(r"`(.*?)`", r"\1", code)  
    return code.strip()

# Function to save AI-generated test cases to a file 📁
def save_tests_to_file(test_code):
    file_path = "generated_tests.py"
    try:
        clean_code = clean_generated_code(test_code)
        with open(file_path, "w") as file:
            file.write("from selenium import webdriver\n")
            file.write("from selenium.webdriver.common.by import By\n")
            file.write("from selenium.webdriver.chrome.service import Service\n")
            file.write("from selenium.webdriver.chrome.options import Options\n")
            file.write("from selenium.webdriver.support.ui import WebDriverWait\n")
            file.write("from selenium.webdriver.support import expected_conditions as EC\n")
            file.write("import pytest\n\n")
            file.write(f'TEST_URL = "{TEST_URL}"\n\n')
            file.write(clean_code)
        return file_path
    except Exception as e:
        print(f"❌ Error saving tests: {e}")
        return None

# Function to execute the generated test file and log results 🚀
def run_selenium_tests(file_path):
    """Runs pytest on the generated test file and captures results."""
    print("🛠️ Running tests in verbose mode...")

    start_time = time.time()
    result = subprocess.run(["pytest", file_path, "-v", "--tb=short", "--durations=10"], 
                            capture_output=True, text=True)
    end_time = time.time()
    overall_execution_time = round(end_time - start_time, 2)

    print(result.stdout)  # Debugging: Print pytest output

    # Parse individual test results
    test_results = parse_pytest_output(result.stdout)  # This should return a list of tuples

    if not test_results:
        print("⚠️ No test results found. Skipping HTML report generation.")
        return False

    # Ensure every result has 3 values (test_name, status, exec_time)
    formatted_results = []
    for test in test_results:
        if len(test) == 2:  # Missing execution time
            test = (*test, 0.0)  # Default exec time as 0.0
        formatted_results.append(test)  # Append correctly

    # Calculate Overall Execution Status
    passed_tests = sum(1 for _, status, _ in formatted_results if "PASSED" in status)
    failed_tests = sum(1 for _, status, _ in formatted_results if "FAILED" in status)
    total_tests = len(formatted_results)

    overall_status = "✅ ALL TESTS PASSED" if failed_tests == 0 else "❌ TESTS FAILED"
    print(f"\n🚀 Overall Status: {overall_status} ({passed_tests}/{total_tests} passed)")

    # Save results to HTML with proper structure
    save_results_to_html(formatted_results, overall_status, overall_execution_time)
    
    print(f"🎉 Test execution completed in {overall_execution_time} sec")

    return True

def parse_pytest_output(output):
    """Parses pytest output to extract test case names, status, and execution time."""
    results = []
    for line in output.split("\n"):
        if "::" in line and ("PASSED" in line or "FAILED" in line or "SKIPPED" in line):
            parts = line.split()
            test_name = parts[0]
            status = parts[1]
            results.append((test_name, status))

    return results

def save_results_to_csv(results):
    """Saves test results to a CSV file."""
    with open("test_results.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Test Case", "Status"])
        writer.writerows(results)
        
def save_test_case_details():
    """Saves generated test cases into a separate HTML page for reference."""
    with open("generated_tests.py", "r") as file:
        code = file.read()

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; padding: 20px; background-color: #f4f4f4; }}
            pre {{ background: #333; color: #fff; padding: 10px; border-radius: 5px; overflow: auto; }}
        </style>
    </head>
    <body>
        <h2>Generated Test Cases</h2>
        <pre>{code}</pre>
        <a href="test_results.html">Back to Test Results</a>
    </body>
    </html>
    """
    with open("test_case_details.html", "w") as file:
        file.write(html_content)

def save_results_to_html(results, overall_status, execution_time):
    """Saves test results to an HTML file with a summary and detailed results."""
    save_test_case_details()
    with open("test_results.html", "w") as file:
        file.write(f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    padding: 20px;
                    background-color: #f4f4f4;
                    text-align: center;
                }}
                h2 {{
                    color: #333;
                }}
                .status {{
                    font-size: 20px;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 5px;
                    display: inline-block;
                    margin-bottom: 15px;
                }}
                .success {{ background-color: #4CAF50; color: white; }}
                .failure {{ background-color: #FF5733; color: white; }}
                table {{
                    width: 80%;
                    margin: auto;
                    border-collapse: collapse;
                    box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                    background: white;
                }}
                th, td {{
                    padding: 12px;
                    border: 1px solid #ddd;
                    text-align: center;
                }}
                th {{
                    background-color: #4CAF50;
                    color: white;
                }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                tr:hover {{ background-color: #f1f1f1; }}
                .passed {{ color: green; font-weight: bold; }}
                .failed {{ color: red; font-weight: bold; }}
                .warning {{ color: orange; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h2>Test Execution Results</h2>
            <div class="status {'success' if 'PASSED' in overall_status else 'failure'}">
                {overall_status}
            </div>
            <p><strong>Execution Time:</strong> {execution_time:.2f} sec</p>
            <table>
                <tr>
                    <th>Test Case</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
        """)

        for test_case, status, exec_time in results:
            status_icon = "✅" if "PASSED" in status else "❌" if "FAILED" in status else "⚠️"
            status_class = "passed" if "PASSED" in status else "failed" if "FAILED" in status else "warning"

            file.write(f"""
                <tr>
                    <td>{test_case}</td>
                    <td class="{status_class}">{status_icon} {status}</td>
                    <td><a href="test_case_details.html">View Code</a></td>
                </tr>
            """)

        file.write("""
            </table>
        </body>
        </html>
        """)

    print("✅ Test results saved to 'test_results.html' successfully!")

# Function to launch Selenium WebDriver and open the hardcoded URL 🌐
def launch_selenium():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service("chromedriver")  
    driver = webdriver.Chrome(service=service, options=options)

    print(f"🚀 Launching browser and opening {TEST_URL}")
    driver.get(TEST_URL)  # Open the hardcoded URL 🌍

    return driver

# Main function (Single Execution) 🎯
def main():
    user_input = recognize_voice()
    if user_input:
        if user_input.lower() in ["exit", "quit", "stop", "thank you", "thanks"]:
            print("🙏 You're welcome! Goodbye! 👋")
            speak("You're welcome! Goodbye!")
            return

        print("⏳ Generating test cases...")
        speak("Generating test cases, please wait.")

        test_cases = get_ai_response(user_input)

        if test_cases:
            speak("Test cases generated. Saving and executing now.")

            test_file = save_tests_to_file(test_cases)
            if test_file:
                success = run_selenium_tests(test_file)
                if success:
                    speak("🎯 Test execution completed successfully.")
                else:
                    speak("⚠️ Test execution failed. Please check the errors.")

    print("✅ Execution completed. Exiting now. 👋")
    speak("Execution completed. Exiting now.")

# Run the main function once 🚀
if __name__ == "__main__":
    main()
