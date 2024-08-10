#
# Robocorp | Automation Certification Level II - Python
# Steve Mellema
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
#
# Future work:
# - output PDF is ugly, and would be nice to have robot image on first page (RPA.PDF is lacking with PDF generation)
# - move locators into a config file?
# - readability and generally being more brief
# - better function names (I used tutorial names)

from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
from RPA.FileSystem import FileSystem

# Webpage to submit robot orders
order_page = "https://robotsparebinindustries.com/#/robot-order"

# Where to download the robot order data CSV
csv_orders_url = "https://robotsparebinindustries.com/orders.csv"

# Where to output the PDF receipts and robot screenshot images
output_receipts_dir = "output/receipts/"

# Where to output robot screenshot images
output_screenshots_dir = "output/screenshots/"

# The final Zip archive containing PDF receipts
output_zip_archive = f"output/receipts.zip"


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the PDF receipts.
    """
    # Clear output directories, removing previous run files
    clear_files()

    # Head to the order page
    browser.goto(order_page)

    # Retrieve the CSV orders
    orders = get_orders()

    # Loop through all orders, filling the form, PDF receipt, and screenshot
    for index, order in enumerate(orders):
        close_annoying_modal()
        fill_the_form(order)
        order_number = get_current_order_number()
        output_pdf_file = store_receipt_as_pdf(order_number)
        screenshot_file = screenshot_robot(order_number)
        embed_screenshot_to_receipt(screenshot_file, output_pdf_file)
        # Now go back to the order page to submit another order
        click_order_another()

    # Finally archive the receipts
    archive_receipts(output_receipts_dir, output_zip_archive)


def clear_files():
    """Clears output directories"""
    fs = FileSystem()
    if fs.does_directory_exist(output_receipts_dir):
        fs.empty_directory(output_receipts_dir)
    if fs.does_directory_exist(output_screenshots_dir):
        fs.empty_directory(output_screenshots_dir)
    fs.remove_file(output_zip_archive)


def get_orders():
    """Downloads the robot orders data in CSV format"""
    local_csv_file = "orders.csv"
    http = HTTP()
    http.download(url=csv_orders_url,
                  target_file=local_csv_file, overwrite=True)

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
    output_pdf = f"{output_receipts_dir}/{order_number}.pdf"
    pdf.html_to_pdf(receipt_html, output_pdf)
    return output_pdf


def screenshot_robot(order_number):
    """Saves image of robot as {order_number}.png"""
    page = browser.page()
    # the rectangle of the robot image div (x, y, width, height)
    image_box = page.locator(
        "//*[@id='robot-preview-image']").bounding_box()
    output_png = f"{output_screenshots_dir}/{order_number}.png"
    # Save the screenshot from the robot bounding_box
    page.screenshot(
        path=output_png,
        clip={'x': image_box['x'],
              'y': image_box['y'],
              'width': image_box['width'],
              'height': image_box['height']})
    return output_png


def embed_screenshot_to_receipt(screenshot_file, pdf_file):
    """Adds a screenshot to the specified PDF"""
    pdf = PDF()
    # The requirements appear to say embed the screenshot in the first page,
    # but I see no way to do that with the API. So we append another page.
    list_of_files = [f"{screenshot_file}:align=center"]
    pdf.add_files_to_pdf(
        files=list_of_files,
        target_document=pdf_file,
        append=True)


def click_order_another():
    """Click Order Another Robot button to go back to order form"""
    page = browser.page()
    page.click("#order-another")


def archive_receipts(source_dir, output_archive):
    """Creates a Zip file of the PDF receipts"""
    fs = FileSystem()
    receipt_files = fs.list_files_in_directory(source_dir)
    archive = Archive()
    archive.archive_folder_with_zip(source_dir, output_archive)
