import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import subprocess
import re
import csv
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth

# Configure Gemini AI
genai.configure(api_key=ENV["API_KEY"])

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty("rate", 150)  # Speech rate

# Function to recognize voice input
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return None
        except sr.RequestError:
            print("Error with speech recognition service.")
            return None

# Function to generate Playwright test cases dynamically
def get_ai_response(test_scenario):
    try:
        model = genai.GenerativeModel("models/gemini-1.5-pro")
        prompt = f"""
        Generate Playwright test cases in Python for the following test scenario: "{test_scenario}".

        - Include positive, negative, and edge cases.
        - Use Playwright with Python.
        - Use text-based, accessibility, or heuristic locators (NO hardcoded IDs).
        - Wrap tests inside a Pytest function with assertions.
        - Use Playwright's `expect` for validation.
        - Ensure **a short wait (`await page.wait_for_timeout(1000)`) between steps** to handle UI rendering delays.
        - Use `page.wait_for_selector()` before interacting with elements to ensure stability.
        - Return only valid Python code, NO explanations or comments.
        - Always launch browser in headed mode not in headless mode
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error in AI response: {e}")
        return None

# Function to clean AI-generated text
def clean_generated_code(code):
    """Removes markdown formatting and invalid syntax from AI response."""
    code = re.sub(r"```python", "", code)  # Remove code block start
    code = re.sub(r"```", "", code)  # Remove code block end
    code = re.sub(r"\*\*(.*?)\*\*", r"\1", code)  # Remove **bold** text
    code = re.sub(r"`(.*?)`", r"\1", code)  # Remove backticks
    return code.strip()

# Function to speak response
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to save AI-generated test cases to a file
def save_tests_to_file(test_code):
    file_path = "generated_tests.py"
    try:
        clean_code = clean_generated_code(test_code)
        with open(file_path, "w") as file:
            file.write("from playwright.sync_api import sync_playwright, expect\n\n")
            file.write("import pytest\n\n")
            file.write(clean_code)
        return file_path
    except Exception as e:
        print(f"Error saving tests: {e}")
        return None

# Function to execute the generated test file and log results
# Function to execute the generated test file and log results in parallel
def run_playwright_tests(file_path, num_workers=4):
    results = []
    try:
        start_time = time.time()
        result = subprocess.run(
            ["pytest", file_path, "--tb=short", "--durations=0", "-n", str(num_workers)], 
            capture_output=True, 
            text=True
        )
        end_time = time.time()
        overall_execution_time = round(end_time - start_time, 2)

        # Extract individual test results with execution time
        test_results = parse_pytest_output(result.stdout)

        # Add test results to CSV log
        results.extend(test_results)

        # Overall status
        overall_status = "Pass" if result.returncode == 0 else "Fail"
        results.append(["Overall Execution", overall_status, f"{overall_execution_time} sec"])

        print(f"Test execution completed: {overall_status} in {overall_execution_time} sec")
        
        save_results_to_csv(results)
        return True
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        overall_execution_time = round(end_time - start_time, 2)

        results.append(["Overall Execution", "Fail", f"{overall_execution_time} sec"])
        print(f"Test execution failed: {e}")
        
        save_results_to_csv(results)
        return False


# Function to parse pytest output for individual test case results and execution time
def parse_pytest_output(output):
    test_results = []
    for line in output.split("\n"):
        match = re.search(r"(\w+)::(\w+) (PASSED|FAILED) in ([\d\.]+)s", line)
        if match:
            test_name = match.group(2)
            status = "Pass" if match.group(3) == "PASSED" else "Fail"
            execution_time = f"{match.group(4)} sec"
            test_results.append([test_name, status, execution_time])
    return test_results

# Function to save results to CSV
def save_results_to_csv(results, filename="test_results.csv"):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Test Case", "Status", "Execution Time"])
        writer.writerows(results)
    print(f"Results saved to {filename}")

# Function to launch Playwright with Mac-compatible User-Agent
def launch_playwright():
    with sync_playwright() as playwright:
        # Launch browser in headed mode for debugging
        browser = playwright.chromium.launch(
            headless=False,  # Set to True if running in CI/CD
            args=[
                "--disable-blink-features=AutomationControlled",  # Prevents detection
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
        )

        # Create a new browser context with anti-CAPTCHA measures
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},  # Set viewport size
            java_script_enabled=True,
            ignore_https_errors=True,  # Ignore SSL issues
            bypass_csp=True,  # Bypass Content Security Policy restrictions
            permissions=["geolocation"],  # Allow location if needed
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/",
            }
        )

        # Modify the `navigator.webdriver` property to evade bot detection
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Create a new page
        page = context.new_page()

        # Return browser, context, and page for further use
        return browser, context, page


# Main function (Single Execution)
def main():
    user_input = recognize_speech()
    if user_input:
        if user_input.lower() in ["exit", "quit", "stop", "thank you", "thanks"]:
            print("You're welcome! Goodbye!")
            speak("You're welcome! Goodbye!")
            return

        print("Generating test cases...")
        speak("Generating test cases, please wait.")

        test_cases = get_ai_response(user_input)

        if test_cases:
            print(f"Generated Test Cases:\n{test_cases}")
            speak("Test cases generated. Saving and executing now.")

            # Save test cases to a file and execute
            test_file = save_tests_to_file(test_cases)
            if test_file:
                success = run_playwright_tests(test_file)
                if success:
                    speak("Test execution completed successfully.")
                else:
                    speak("Test execution failed. Please check the errors.")

    print("Execution completed. Exiting now.")
    speak("Execution completed. Exiting now.")

# Run the main function once
if __name__ == "__main__":
    main()
