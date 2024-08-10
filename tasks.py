# Robocorp | Automation Certification Level II - Python
#
# Requirements:
# https://robocorp.com/docs/courses/build-a-robot-python/rules-for-the-robot
#
# The robot should use the orders file (.csv) and complete all the orders in the file. -- https://robotsparebinindustries.com/orders.csv
# Only the robot is allowed to get the orders file. You may not save the file manually on your computer.
# The robot should save each order HTML receipt as a PDF file.
# The robot should save a screenshot of each of the ordered robots.
# The robot should embed the screenshot of the robot to the PDF receipt.
# The robot should create a ZIP archive of the PDF receipts(one zip archive that contains all the PDF files). Store the archive in the output directory.
# The robot should complete all the orders even when there are technical failures with the robot order website.
# The robot should be available in public GitHub repository.
# It should be possible to get the robot from the public GitHub repository and run it without manual setup.

from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF

# Webpage to submit robot orders
order_page = "https://robotsparebinindustries.com/#/robot-order"

# Where to download the robot order data CSV
csv_url = "https://robotsparebinindustries.com/orders.csv"


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.goto(order_page)
    orders = get_orders()
    close_annoying_modal()
    for index, order in enumerate(orders):
        fill_the_form(order)
        order_number = get_current_order_number()
        store_receipt_as_pdf(order_number)
        click_order_another()

        # TODO save screenshot
        # TODO embed screenshot in PDF

        # The modal pops again sometimes when going to order another
        close_annoying_modal()

    # TODO create Zip archive of all receipts and images


def get_orders():
    """Downloads the robot orders data in CSV format"""
    local_csv_file = "orders.csv"
    http = HTTP()
    http.download(url=csv_url, target_file=local_csv_file, overwrite=True)

    # Read the CSV file into a table
    tables = Tables()
    return tables.read_table_from_csv(local_csv_file)


def close_annoying_modal():
    """Closes the page modal by clicking OK"""
    page = browser.page()
    # Only one "OK" button on the page
    page.click("button:text('OK')")


def fill_the_form(order):
    """Fill and submit the order (Head, Body, Legs, Address)"""
    page = browser.page()
    page.select_option("#head", order['Head'])
    page.check(f"#id-body-{order['Body']}")
    # the Legs input element id changes
    page.fill("//input[@class='form-control'][1]", order['Legs'])
    page.fill("#address", order['Address'])
    page.click("#preview")
    page.click("#order")
    # If error, need to repeat Order click
    while (page.is_visible("//div[contains(@class, 'alert-danger')]")):
        page.click("#order")


def get_current_order_number():
    """Get order number from the receipt page"""
    page = browser.page()
    return page.text_content("//*[@id='receipt']/p[1]")


def store_receipt_as_pdf(order_number):
    """Save order receipt HTML as order_number.pdf"""
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()
    pdf = PDF()
    pdf.html_to_pdf(receipt_html, f"output/receipts/{order_number}.pdf")


def click_order_another():
    """Click Order Another Robot to go back to order form"""
    page = browser.page()
    page.click("#order-another")
