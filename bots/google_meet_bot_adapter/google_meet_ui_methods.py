from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class UiException(Exception):
    def __init__(self, message, step, original_exception):
        self.step = step
        self.original_exception = original_exception
        super().__init__(message)


class UiRetryableException(UiException):
    def __init__(self, message, step=None, original_exception=None):
        super().__init__(message, step, original_exception)


# When this exception is raised, the bot will stop running and it will take a screenshot
# of the UI to help with debugging
class UiFatalException(UiException):
    def __init__(self, message, step=None, original_exception=None):
        super().__init__(message, step, original_exception)


# When this exception is raised, the bot will stop running and log that it was denied access to the meeting
class UiRequestToJoinDeniedException(UiFatalException):
    def __init__(self, message, step=None, original_exception=None):
        super().__init__(message, step, original_exception)


class GoogleMeetUIMethods:
    def locate_element(self, step, condition, wait_time_seconds=60):
        try:
            element = WebDriverWait(self.driver, wait_time_seconds).until(condition)
            return element
        except Exception as e:
            # Take screenshot when any exception occurs
            print(f"Exception raised in locate_element for {step}")
            raise UiFatalException(
                f"Exception raised in locate_element for {step}", step, e
            )

    def find_element_by_selector(self, selector_type, selector):
        try:
            return self.driver.find_element(selector_type, selector)
        except NoSuchElementException:
            return None

    def look_for_blocked_element(self, step):
        cannot_join_element = self.find_element_by_selector(
            By.XPATH, '//*[contains(text(), "You can\'t join this video call")]'
        )
        if cannot_join_element:
            # This means google is blocking us for whatever reason, but we can retry
            print(
                "Google is blocking us for whatever reason, but we can retry. Raising UiRetryableException"
            )
            raise UiRetryableException("You can't join this video call", step)

    def look_for_denied_your_request_element(self, step):
        denied_your_request_element = self.find_element_by_selector(
            By.XPATH,
            '//*[contains(text(), "Someone in the call denied your request to join")]',
        )
        if denied_your_request_element:
            print(
                "Someone in the call denied our request to join. Raising UiRequestToJoinDeniedException"
            )
            raise UiRequestToJoinDeniedException(
                "Someone in the call denied your request to join", step
            )

    def fill_out_name_input(self):
        num_attempts_to_look_for_name_input = 30
        print("Waiting for the name input field...")
        for attempt_to_look_for_name_input_index in range(
            num_attempts_to_look_for_name_input
        ):
            try:
                name_input = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'input[type="text"][aria-label="Your name"]')
                    )
                )
                print("name input found")
                name_input.send_keys(self.display_name)
                return
            except TimeoutException as e:
                self.look_for_blocked_element("name_input")

                last_check_timed_out = (
                    attempt_to_look_for_name_input_index
                    == num_attempts_to_look_for_name_input - 1
                )
                if last_check_timed_out:
                    print(
                        "Could not find name input. Timed out. Raising UiFatalException"
                    )
                    raise UiFatalException(
                        "Could not find name input. Timed out.", "name_input", e
                    )

            except Exception as e:
                print(
                    "Could not find name input. Unknown error. Raising UiFatalException"
                )
                raise UiFatalException(
                    "Could not find name input. Unknown error.", "name_input", e
                )

    def click_captions_button(self):
        num_attempts_to_look_for_captions_button = 120
        print("Waiting for captions button...")
        for attempt_to_look_for_captions_button_index in range(
            num_attempts_to_look_for_captions_button
        ):
            try:
                captions_button = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'button[aria-label="Turn on captions"]')
                    )
                )
                print("Captions button found")
                captions_button.click()
                return
            except TimeoutException as e:
                self.look_for_blocked_element("click_captions_button")
                self.look_for_denied_your_request_element("click_captions_button")

                last_check_timed_out = (
                    attempt_to_look_for_captions_button_index
                    == num_attempts_to_look_for_captions_button - 1
                )
                if last_check_timed_out:
                    print(
                        "Could not find captions button. Timed out. Raising UiFatalException"
                    )
                    raise UiFatalException(
                        "Could not find captions button. Timed out.",
                        "click_captions_button",
                        e,
                    )

            except Exception as e:
                print(
                    "Could not find captions button. Unknown error. Raising UiFatalException"
                )
                raise UiFatalException(
                    "Could not find captions button. Unknown error.",
                    "click_captions_button",
                    e,
                )

    # returns nothing if succeeded, raises an exception if failed
    def attempt_to_join_meeting(self):
        self.driver.get(self.meeting_url)

        self.driver.execute_cdp_cmd(
            "Browser.grantPermissions",
            {
                "origin": self.meeting_url,
                "permissions": [
                    "geolocation",
                    "audioCapture",
                    "displayCapture",
                    "videoCapture",
                    "videoCapturePanTiltZoom",
                ],
            },
        )

        self.fill_out_name_input()

        print("Waiting for the 'Ask to join' button...")
        join_button = self.locate_element(
            step="join_button",
            condition=EC.presence_of_element_located(
                (By.XPATH, '//button[.//span[text()="Ask to join"]]')
            ),
            wait_time_seconds=60,
        )
        print("Clicking the 'Ask to join' button...")
        join_button.click()

        self.click_captions_button()

        print("Waiting for the more options button...")
        MORE_OPTIONS_BUTTON_SELECTOR = (
            'button[jsname="NakZHc"][aria-label="More options"]'
        )
        more_options_button = self.locate_element(
            step="more_options_button",
            condition=EC.presence_of_element_located(
                (By.CSS_SELECTOR, MORE_OPTIONS_BUTTON_SELECTOR)
            ),
            wait_time_seconds=6,
        )
        print("Clicking the more options button...")
        more_options_button.click()

        print("Waiting for the 'Change layout' list item...")
        change_layout_list_item = self.locate_element(
            step="change_layout_item",
            condition=EC.presence_of_element_located(
                (By.XPATH, '//li[.//span[text()="Change layout"]]')
            ),
            wait_time_seconds=6,
        )
        print("Clicking the 'Change layout' list item...")
        change_layout_list_item.click()

        print("Waiting for the 'Spotlight' label element")
        spotlight_label = self.locate_element(
            step="spotlight_label",
            condition=EC.presence_of_element_located(
                (By.XPATH, '//label[.//span[text()="Spotlight"]]')
            ),
            wait_time_seconds=6,
        )
        print("Clicking the 'Spotlight' label element")
        spotlight_label.click()

        print("Waiting for the close button")
        close_button = self.locate_element(
            step="close_button",
            condition=EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'button[aria-label="Close"]')
            ),
            wait_time_seconds=6,
        )
        print("Clicking the close button")
        close_button.click()
